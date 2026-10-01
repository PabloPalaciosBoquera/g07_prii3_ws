import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from turtlesim.srv import TeleportAbsolute, SetPen
from std_srvs.srv import Trigger


class Dibujar7(Node):

    def __init__(self):
        super().__init__('dibujar_7')

        # ============================================================
        # PUBLISHER
        # ============================================================

        # Publicador para controlar la velocidad de turtle1
        self.publisher = self.create_publisher(
            Twist,
            '/turtle1/cmd_vel',
            10
        )

        # ============================================================
        # SUBSCRIBER
        # ============================================================

        # Suscripción para conocer la posición actual de turtle1
        self.subscription = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self.pose_callback,
            10
        )

        # ============================================================
        # CLIENTES DE SERVICIOS DE TURTLESIM
        # ============================================================

        # Servicio para colocar la tortuga en la posición inicial
        self.teleport_client = self.create_client(
            TeleportAbsolute,
            '/turtle1/teleport_absolute'
        )

        # Servicio para encender y apagar el lápiz
        self.pen_client = self.create_client(
            SetPen,
            '/turtle1/set_pen'
        )

        # ============================================================
        # SERVICIOS DE CONTROL DEL DIBUJO
        # ============================================================

        self.servicio_detener = self.create_service(
            Trigger,
            'detener_dibujo',
            self.detener_callback
        )

        self.servicio_reanudar = self.create_service(
            Trigger,
            'reanudar_dibujo',
            self.reanudar_callback
        )

        self.servicio_reiniciar = self.create_service(
            Trigger,
            'reiniciar_dibujo',
            self.reiniciar_callback
        )

        # ============================================================
        # VARIABLES
        # ============================================================

        self.pose = None

        # Recorrido completo del número 7
        self.puntos = [
            (2.0, 10.0),   # Punto inicial
            (10.0, 10.0),  # Línea horizontal superior
            (7.0, 6.0),    # Diagonal
            (5.0, 6.0),    # Horizontal hacia la izquierda
            (9.0, 6.0),    # Horizontal hacia la derecha
            (7.0, 6.0),    # Volver al centro
            (4.0, 2.0),    # Diagonal final
        ]

        # El punto 0 es la posición inicial.
        # Por tanto, empezamos dirigiéndonos al punto 1.
        self.objetivo_actual = 1

        # Estados del programa
        self.inicializado = False
        self.inicializando = False
        self.terminado = False
        self.pausado = False

        # Ejecutar el controlador cada 0.05 segundos
        self.timer = self.create_timer(
            0.05,
            self.control
        )

        self.get_logger().info(
            'Nodo Dibujar7 iniciado'
        )

    # ================================================================
    # POSICIÓN
    # ================================================================

    def pose_callback(self, msg):
        """
        Guarda la posición actual de la tortuga.
        """
        self.pose = msg

    # ================================================================
    # CONTROL DEL LÁPIZ
    # ================================================================

    def configurar_lapiz(self, apagado):
        """
        Enciende o apaga el lápiz de turtlesim.
        """

        request = SetPen.Request()

        # Color blanco
        request.r = 255
        request.g = 255
        request.b = 255

        # Grosor de línea
        request.width = 3

        # 1 = apagado
        # 0 = encendido
        request.off = 1 if apagado else 0

        return self.pen_client.call_async(request)

    # ================================================================
    # POSICIÓN INICIAL
    # ================================================================

    def colocar_inicio(self):
        """
        Coloca la tortuga en (2,10) sin dibujar
        desde la posición donde aparece inicialmente.
        """

        if self.inicializando:
            return

        # Esperamos a que los servicios estén disponibles
        if not self.teleport_client.service_is_ready():
            return

        if not self.pen_client.service_is_ready():
            return

        self.inicializando = True

        # Primero apagamos el lápiz
        future_pen = self.configurar_lapiz(True)

        future_pen.add_done_callback(
            self.lapiz_apagado
        )

    def lapiz_apagado(self, future):
        """
        Cuando el lápiz está apagado,
        teletransportamos la tortuga.
        """

        request = TeleportAbsolute.Request()

        request.x = self.puntos[0][0]
        request.y = self.puntos[0][1]

        # Empieza mirando hacia la derecha
        request.theta = 0.0

        future_teleport = self.teleport_client.call_async(
            request
        )

        future_teleport.add_done_callback(
            self.teleportado
        )

    def teleportado(self, future):
        """
        Una vez teletransportada,
        volvemos a encender el lápiz.
        """

        future_pen = self.configurar_lapiz(False)

        future_pen.add_done_callback(
            self.lapiz_encendido
        )

    def lapiz_encendido(self, future):
        """
        Finaliza la inicialización.
        """

        self.inicializado = True
        self.inicializando = False

        self.get_logger().info(
            'Tortuga colocada en (2,10). Comenzando dibujo.'
        )

    # ================================================================
    # CONTROL PRINCIPAL DEL MOVIMIENTO
    # ================================================================

    def control(self):
        """
        Controla automáticamente el movimiento de la tortuga.
        """

        # Si todavía no está colocada en el inicio
        if not self.inicializado:
            self.colocar_inicio()
            return

        # Si todavía no conocemos su posición
        if self.pose is None:
            return

        # Si el dibujo ya ha terminado
        if self.terminado:
            return

        # Si el dibujo está pausado
        if self.pausado:
            self.parar()
            return

        # Comprobar si ya hemos recorrido todos los puntos
        if self.objetivo_actual >= len(self.puntos):

            self.parar()

            self.terminado = True

            self.get_logger().info(
                'Número 7 terminado'
            )

            return

        # ============================================================
        # SIGUIENTE OBJETIVO
        # ============================================================

        objetivo_x, objetivo_y = self.puntos[
            self.objetivo_actual
        ]

        # Diferencia entre posición actual y objetivo
        dx = objetivo_x - self.pose.x
        dy = objetivo_y - self.pose.y

        # Distancia al objetivo
        distancia = math.hypot(
            dx,
            dy
        )

        # ============================================================
        # COMPROBAR SI HEMOS LLEGADO
        # ============================================================

        if distancia < 0.08:

            self.parar()

            self.get_logger().info(
                f'Punto {self.objetivo_actual} alcanzado: '
                f'({objetivo_x}, {objetivo_y})'
            )

            # Pasar al siguiente punto
            self.objetivo_actual += 1

            return

        # ============================================================
        # CALCULAR DIRECCIÓN
        # ============================================================

        angulo_objetivo = math.atan2(
            dy,
            dx
        )

        error_angulo = (
            angulo_objetivo - self.pose.theta
        )

        # Normalizar el ángulo entre -pi y pi
        error_angulo = math.atan2(
            math.sin(error_angulo),
            math.cos(error_angulo)
        )

        msg = Twist()

        # ============================================================
        # GIRAR O AVANZAR
        # ============================================================

        # Si todavía está mal orientada,
        # gira sin avanzar
        if abs(error_angulo) > 0.05:

            msg.linear.x = 0.0

            msg.angular.z = (
                2.0 * error_angulo
            )

        else:

            # Si está correctamente orientada, avanza
            msg.linear.x = 1.5

            # Corrige ligeramente la dirección mientras avanza
            msg.angular.z = (
                1.5 * error_angulo
            )

        self.publisher.publish(msg)

    # ================================================================
    # SERVICIO: DETENER
    # ================================================================

    def detener_callback(self, request, response):
        """
        Pausa el dibujo en la posición actual.
        """

        self.pausado = True

        self.parar()

        response.success = True
        response.message = 'Dibujo detenido'

        self.get_logger().info(
            'Dibujo detenido'
        )

        return response

    # ================================================================
    # SERVICIO: REANUDAR
    # ================================================================

    def reanudar_callback(self, request, response):
        """
        Continúa el dibujo desde donde se había detenido.
        """

        if self.terminado:

            response.success = False
            response.message = (
                'El dibujo ya ha terminado. '
                'Utiliza reiniciar_dibujo.'
            )

            return response

        if not self.pausado:

            response.success = False
            response.message = (
                'El dibujo no está detenido'
            )

            return response

        self.pausado = False

        response.success = True
        response.message = 'Dibujo reanudado'

        self.get_logger().info(
            'Dibujo reanudado'
        )

        return response

    # ================================================================
    # SERVICIO: REINICIAR
    # ================================================================

    def reiniciar_callback(self, request, response):
        """
        Reinicia completamente el recorrido.
        """

        # Detener primero la tortuga
        self.parar()

        # Volver al primer objetivo
        self.objetivo_actual = 1

        # Restablecer estados
        self.terminado = False
        self.pausado = False

        # Esto provoca que control() vuelva a ejecutar:
        # apagar lápiz -> teleportar -> encender lápiz
        self.inicializado = False
        self.inicializando = False

        response.success = True
        response.message = 'Dibujo reiniciado'

        self.get_logger().info(
            'Reiniciando dibujo'
        )

        return response

    # ================================================================
    # DETENER MOVIMIENTO
    # ================================================================

    def parar(self):
        """
        Envía velocidad cero a la tortuga.
        """

        msg = Twist()

        msg.linear.x = 0.0
        msg.angular.z = 0.0

        self.publisher.publish(msg)


# ====================================================================
# MAIN
# ====================================================================

def main(args=None):

    rclpy.init(args=args)

    nodo = Dibujar7()

    try:
        rclpy.spin(nodo)

    except KeyboardInterrupt:
        pass

    # Detener la tortuga antes de cerrar
    nodo.parar()

    nodo.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
