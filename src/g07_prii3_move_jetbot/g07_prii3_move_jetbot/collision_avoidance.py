import math
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from std_srvs.srv import Trigger

# Recorrido del numero 7
RECTA = 0.50
DIAGONAL = 0.73
ANGULO_DIAGONAL = -1.85  # Aproximadamente 106 grados a la derecha

# Deteccion de obstaculos
DISTANCIA_PARADA = 0.35  # metros
ANGULO_FRONTAL = 25     # grados hacia cada lado


class CollisionAvoidance(Node):

    def __init__(self):
        super().__init__('collision_avoidance')

        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)

        self.create_service(Trigger, 'detener_dibujo', self.detener_callback)
        self.create_service(Trigger, 'reanudar_dibujo', self.reanudar_callback)
        self.create_service(Trigger, 'reiniciar_dibujo', self.reiniciar_callback)

        self.x = None
        self.y = None
        self.angulo = 0.0
        self.x_inicio = 0.0
        self.y_inicio = 0.0
        self.angulo_inicio = 0.0
        self.x_tramo = 0.0
        self.y_tramo = 0.0

        self.ultima_odom = time.monotonic()
        self.ultima_scan = None
        self.scan = None
        self.distancia_frontal = None
        self.hay_obstaculo = False
        self.bloqueado_desde = None

        self.fase = 'recta'
        self.pausado = True  # Empieza parado: usar el servicio reanudar para moverlo.
        self.error_seguridad = False
        self.inicio_fase = time.monotonic()

        self.create_timer(0.05, self.control)

    def odom_callback(self, msg):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation
        angulo = 2 * math.atan2(q.z, q.w)

        if self.x is None:
            self.x_inicio = x
            self.y_inicio = y
            self.angulo_inicio = angulo
            self.x_tramo = x
            self.y_tramo = y
            self.inicio_fase = time.monotonic()

        self.x = x
        self.y = y
        self.angulo = angulo
        self.ultima_odom = time.monotonic()

    def scan_callback(self, msg):
        self.scan = msg
        self.ultima_scan = time.monotonic()

        # Distancia mas cercana frente al LiDAR (de -25 a +25 grados).
        minima = None

        for i, distancia in enumerate(msg.ranges):
            angulo = math.degrees(
                msg.angle_min + i * msg.angle_increment
            ) % 360

            if 180 - ANGULO_FRONTAL <= angulo <= 180 + ANGULO_FRONTAL:
                if (math.isfinite(distancia)
                        and 0.0 < distancia <= msg.range_max):
                    if minima is None or distancia < minima:
                        minima = distancia

        antes = self.hay_obstaculo
        self.distancia_frontal = minima
        self.hay_obstaculo = minima is not None and minima < DISTANCIA_PARADA

        # Mostrar cuando aparece/desaparece un obstaculo (incluso en pausa).
        if self.hay_obstaculo and not antes:
            self.get_logger().warn(
                'OBSTACULO A ' + str(round(minima, 2)) + ' m: PARADA'
            )
        elif antes and not self.hay_obstaculo:
            self.get_logger().info('Camino libre')

    def obstaculo_delante(self):
        return self.hay_obstaculo

    def mover(self, avance, giro):
        msg = Twist()
        msg.linear.x = float(avance)
        msg.angular.z = float(giro)
        self.publisher.publish(msg)

    def error_angulo(self, destino):
        error = destino - self.angulo
        return math.atan2(math.sin(error), math.cos(error))

    def parada_seguridad(self, motivo):
        self.error_seguridad = True
        self.mover(0.0, 0.0)
        self.get_logger().error('PARADA: ' + motivo)

    def control(self):
        if self.x is None:
            self.mover(0.0, 0.0)
            return

        ahora = time.monotonic()

        if ahora - self.ultima_odom > 0.5:
            if not self.error_seguridad:
                self.parada_seguridad('Sin odometria')
            self.mover(0.0, 0.0)
            return

        if self.ultima_scan is None or ahora - self.ultima_scan > 1.0:
            if self.ultima_scan is not None and not self.error_seguridad:
                self.parada_seguridad('Sin datos del LiDAR')
            self.mover(0.0, 0.0)
            return

        if self.pausado or self.error_seguridad or self.fase == 'fin':
            self.mover(0.0, 0.0)
            return

        # IMPORTANTE: comprobar el obstaculo ANTES de cualquier movimiento,
        # tambien durante la fase de giro y cuando vuelve al inicio.
        if self.obstaculo_delante():
            if self.bloqueado_desde is None:
                self.bloqueado_desde = ahora
            self.mover(0.0, 0.0)
            return

        # No contar el tiempo que estuvo parado por un obstaculo.
        if self.bloqueado_desde is not None:
            self.inicio_fase += ahora - self.bloqueado_desde
            self.bloqueado_desde = None

        if self.fase == 'recta':
            limite = 13
        elif self.fase == 'diagonal':
            limite = 18
        elif self.fase == 'volver':
            limite = 30
        else:
            limite = 12

        if ahora - self.inicio_fase > limite:
            self.parada_seguridad('Tiempo maximo superado')
            return

        # Primera recta y diagonal: mantener un rumbo estable.
        if self.fase == 'recta' or self.fase == 'diagonal':
            distancia = math.hypot(self.x - self.x_tramo, self.y - self.y_tramo)

            if self.fase == 'recta':
                meta = RECTA
                direccion = self.angulo_inicio
            else:
                meta = DIAGONAL
                direccion = self.angulo_inicio + ANGULO_DIAGONAL

            if distancia >= meta - 0.02:
                self.mover(0.0, 0.0)
                if self.fase == 'recta':
                    self.fase = 'giro'
                    self.get_logger().info('Recta terminada. Girando.')
                else:
                    self.fase = 'fin'
                    self.get_logger().info('Numero 7 terminado.')
                self.inicio_fase = ahora
                return

            error = self.error_angulo(direccion)
            if abs(error) > 0.55:
                self.parada_seguridad('Se ha desviado demasiado')
                return

            avance = 0.07 if meta - distancia < 0.10 else 0.10
            giro = max(-0.12, min(0.12, 0.6 * error))
            self.mover(avance, giro)
            return

        # Giro de la esquina y orientacion inicial tras reiniciar.
        if self.fase == 'giro' or self.fase == 'orientar':
            if self.fase == 'giro':
                direccion = self.angulo_inicio + ANGULO_DIAGONAL
            else:
                direccion = self.angulo_inicio

            error = self.error_angulo(direccion)

            if abs(error) < 0.14:
                if self.fase == 'giro':
                    self.fase = 'diagonal'
                else:
                    self.fase = 'recta'
                self.x_tramo = self.x
                self.y_tramo = self.y
                self.inicio_fase = ahora
                self.mover(0.0, 0.0)
                return

            if error > 0:
                self.mover(0.0, 0.30)
            else:
                self.mover(0.0, -0.30)
            return

        # Reinicio: volver al punto de partida.
        if self.fase == 'volver':
            distancia = math.hypot(self.x_inicio - self.x, self.y_inicio - self.y)
            if distancia < 0.06:
                self.fase = 'orientar'
                self.inicio_fase = ahora
                self.mover(0.0, 0.0)
                return

            direccion = math.atan2(self.y_inicio - self.y, self.x_inicio - self.x)
            error = self.error_angulo(direccion)
            if abs(error) > 0.15:
                if error > 0:
                    self.mover(0.0, 0.30)
                else:
                    self.mover(0.0, -0.30)
            else:
                self.mover(0.07, max(-0.10, min(0.10, 0.6 * error)))

    def detener_callback(self, request, response):
        self.pausado = True
        self.bloqueado_desde = None
        self.mover(0.0, 0.0)
        response.success = True
        response.message = 'Dibujo detenido'
        return response

    def reanudar_callback(self, request, response):
        if self.error_seguridad:
            response.success = False
            response.message = 'Parada de seguridad. Revisar y reiniciar el nodo.'
        else:
            self.pausado = False
            self.bloqueado_desde = None
            self.inicio_fase = time.monotonic()
            response.success = True
            response.message = 'Dibujo reanudado'
        return response

    def reiniciar_callback(self, request, response):
        if self.error_seguridad:
            response.success = False
            response.message = 'Parada de seguridad. Revisar y reiniciar el nodo.'
        else:
            self.fase = 'volver'
            self.pausado = False
            self.bloqueado_desde = None
            self.inicio_fase = time.monotonic()
            response.success = True
            response.message = 'Volviendo al inicio'
        return response


def main():
    rclpy.init()
    nodo = CollisionAvoidance()
    try:
        rclpy.spin(nodo)
    except KeyboardInterrupt:
        pass
    finally:
        for i in range(5):
            nodo.mover(0.0, 0.0)
            time.sleep(0.05)
        nodo.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
