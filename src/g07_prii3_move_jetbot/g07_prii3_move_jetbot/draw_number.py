import math
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_srvs.srv import Trigger


# Coordenadas respecto a la posicion y orientacion inicial del robot.
PUNTOS = [(0.0, 0.0), (0.50, 0.0), (0.30, -0.70)]


def normalizar(angulo):
    return math.atan2(math.sin(angulo), math.cos(angulo))


def limitar(valor, minimo, maximo):
    return max(minimo, min(maximo, valor))


class DrawNumber(Node):
    def __init__(self):
        super().__init__('draw_number')

        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.create_service(Trigger, 'detener_dibujo', self.detener_callback)
        self.create_service(Trigger, 'reanudar_dibujo', self.reanudar_callback)
        self.create_service(Trigger, 'reiniciar_dibujo', self.reiniciar_callback)

        self.inicio = None
        self.angulo_inicial = None
        self.ultima_odom = None
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0

        self.objetivo = 1
        self.fase = 'avanzar'  # Al principio no gira.
        self.pausado = False
        self.error_seguridad = False

        # Referencias para medir la distancia REAL de cada tramo.
        self.inicio_tramo = None
        self.tiempo_fase = time.monotonic()
        self.ultimo_mensaje = time.monotonic()

        self.create_timer(0.05, self.control)

    def odom_callback(self, msg):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        q = msg.pose.pose.orientation

        angulo = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        )

        if self.inicio is None:
            self.inicio = (x, y)
            self.angulo_inicial = angulo

        dx = x - self.inicio[0]
        dy = y - self.inicio[1]
        c = math.cos(self.angulo_inicial)
        s = math.sin(self.angulo_inicial)

        self.x = c * dx + s * dy
        self.y = -s * dx + c * dy
        self.theta = normalizar(angulo - self.angulo_inicial)
        self.ultima_odom = time.monotonic()

        if self.inicio_tramo is None:
            self.inicio_tramo = (self.x, self.y)
            self.tiempo_fase = time.monotonic()

    def parada_seguridad(self, motivo):
        self.error_seguridad = True
        self.pausado = True
        self.mover(0.0, 0.0)
        self.get_logger().error('PARADA DE SEGURIDAD: ' + motivo)

    def control(self):
        if self.inicio is None:
            self.mover(0.0, 0.0)
            return

        if self.ultima_odom is None or time.monotonic() - self.ultima_odom > 0.5:
            if not self.error_seguridad:
                self.parada_seguridad('No llegan datos recientes de odometria')
            else:
                self.mover(0.0, 0.0)
            return

        if self.pausado or self.error_seguridad or self.objetivo >= len(PUNTOS):
            self.mover(0.0, 0.0)
            return

        ahora = time.monotonic()

        # Reiniciar vuelve al origen original del recorrido.
        if self.objetivo == 0:
            if ahora - self.tiempo_fase > 30.0:
                self.parada_seguridad('Tiempo maximo regresando al origen')
                return

            distancia = math.hypot(self.x, self.y)
            if distancia < 0.06:
                self.objetivo = 1
                self.fase = 'girar'
                self.tiempo_fase = ahora
                self.mover(0.0, 0.0)
                return

            direccion = math.atan2(-self.y, -self.x)
            error = normalizar(direccion - self.theta)
            if abs(error) > 0.15:
                giro = limitar(error, -0.35, 0.35)
                if abs(giro) < 0.18:
                    giro = math.copysign(0.18, error)
                self.mover(0.0, giro)
            else:
                self.mover(0.07, limitar(0.6 * error, -0.10, 0.10))
            return

        origen_x, origen_y = PUNTOS[self.objetivo - 1]
        destino_x, destino_y = PUNTOS[self.objetivo]
        vx = destino_x - origen_x
        vy = destino_y - origen_y
        longitud = math.hypot(vx, vy)
        direccion = math.atan2(vy, vx)
        error = normalizar(direccion - self.theta)

        if self.fase == 'girar':
            # Esperar menos: tolerancia 0.14 rad (unos 8 grados).
            if ahora - self.tiempo_fase > 12.0:
                self.parada_seguridad('El giro no termina en 12 segundos')
                return

            if abs(error) > 0.14:
                giro = limitar(0.9 * error, -0.38, 0.38)
                # Evitar una velocidad angular demasiado pequena para los motores.
                if abs(giro) < 0.18:
                    giro = math.copysign(0.18, error)
                self.mover(0.0, giro)
                return

            self.fase = 'avanzar'
            self.inicio_tramo = (self.x, self.y)
            self.tiempo_fase = ahora
            self.mover(0.0, 0.0)
            self.get_logger().info('Giro completado: empieza tramo %d' % self.objetivo)
            return

        # El avance se mide desde el comienzo del tramo, no proyectando
        # sobre la linea ideal, lo que podia impedir que terminara.
        recorrido = math.hypot(
            self.x - self.inicio_tramo[0],
            self.y - self.inicio_tramo[1]
        )
        restante = longitud - recorrido

        if ahora - self.ultimo_mensaje > 1.0:
            self.get_logger().info(
                'Tramo %d: %.2f / %.2f m (error giro %.1f grados)' % (
                    self.objetivo, recorrido, longitud, math.degrees(error)
                )
            )
            self.ultimo_mensaje = ahora

        if restante <= 0.02:
            self.mover(0.0, 0.0)
            self.objetivo += 1
            if self.objetivo >= len(PUNTOS):
                self.get_logger().info('NUMERO 7 TERMINADO. Robot detenido.')
            else:
                self.fase = 'girar'
                self.tiempo_fase = ahora
                self.get_logger().info('Primera linea terminada: girando a la derecha')
            return

        # Tiempo maximo por tramo para que no avance indefinidamente.
        tiempo_maximo = 13.0 if self.objetivo == 1 else 18.0
        if ahora - self.tiempo_fase > tiempo_maximo:
            self.parada_seguridad('No se completo el tramo dentro del tiempo maximo')
            return

        # Si se desorienta mucho, parar por seguridad.
        if abs(error) > 0.55:
            self.parada_seguridad('Desviacion excesiva durante el avance')
            return

        velocidad = 0.07 if restante < 0.10 else 0.10
        giro_suave = limitar(0.6 * error, -0.12, 0.12)
        self.mover(velocidad, giro_suave)

    def detener_callback(self, request, response):
        self.pausado = True
        self.mover(0.0, 0.0)
        response.success = True
        response.message = 'Dibujo detenido'
        return response

    def reanudar_callback(self, request, response):
        if self.error_seguridad:
            response.success = False
            response.message = 'Parada de seguridad: revise el robot y reinicie el nodo'
        else:
            self.pausado = False
            self.tiempo_fase = time.monotonic()
            response.success = True
            response.message = 'Dibujo reanudado'
        return response

    def reiniciar_callback(self, request, response):
        if self.error_seguridad:
            response.success = False
            response.message = 'Parada de seguridad: revise el robot y reinicie el nodo'
        else:
            self.objetivo = 0
            self.fase = 'volver'
            self.pausado = False
            self.tiempo_fase = time.monotonic()
            response.success = True
            response.message = 'Volviendo al origen para reiniciar el dibujo'
        return response

    def mover(self, lineal, angular):
        msg = Twist()
        msg.linear.x = float(lineal)
        msg.angular.z = float(angular)
        self.publisher.publish(msg)


def main():
    rclpy.init()
    nodo = DrawNumber()
    try:
        rclpy.spin(nodo)
    except KeyboardInterrupt:
        pass
    finally:
        for _ in range(5):
            nodo.mover(0.0, 0.0)
            time.sleep(0.05)
        nodo.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
