import math

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry
from std_srvs.srv import Trigger


# Puntos del 7 en metros: línea de arriba y diagonal
PUNTOS = [(0.0, 0.0), (0.8, 0.0), (0.3, -0.8)]


class DrawNumber(Node):

    def __init__(self):
        super().__init__('draw_number')

        self.publisher = self.create_publisher(TwistStamped, '/cmd_vel', 10)
        self.create_subscription(Odometry, '/odom', self.odom_callback, 10)

        self.create_service(Trigger, 'detener_dibujo', self.detener_callback)
        self.create_service(Trigger, 'reanudar_dibujo', self.reanudar_callback)
        self.create_service(Trigger, 'reiniciar_dibujo', self.reiniciar_callback)

        self.inicio = None   # Posición donde empieza el robot
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.objetivo = 1    # Índice del punto al que va
        self.pausado = False

        self.create_timer(0.05, self.control)

    def odom_callback(self, msg):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        if self.inicio is None:
            self.inicio = (x, y)
        self.x = x - self.inicio[0]
        self.y = y - self.inicio[1]
        q = msg.pose.pose.orientation
        self.theta = 2 * math.atan2(q.z, q.w)

    def control(self):
        if self.inicio is None:
            return
        if self.pausado or self.objetivo >= len(PUNTOS):
            self.mover(0.0, 0.0)
            return

        objetivo_x, objetivo_y = PUNTOS[self.objetivo]
        dx = objetivo_x - self.x
        dy = objetivo_y - self.y

        # Ha llegado al punto: pasa al siguiente
        if math.hypot(dx, dy) < 0.05:
            self.objetivo += 1
            return

        error = math.atan2(dy, dx) - self.theta
        error = math.atan2(math.sin(error), math.cos(error))

        if abs(error) > 0.1:
            # Gira hasta mirar al punto
            if error > 0:
                self.mover(0.0, 0.5)
            else:
                self.mover(0.0, -0.5)
        else:
            # Avanza hacia el punto
            self.mover(0.12, 0.0)

    def detener_callback(self, request, response):
        self.pausado = True
        response.success = True
        response.message = 'Dibujo detenido'
        return response

    def reanudar_callback(self, request, response):
        self.pausado = False
        response.success = True
        response.message = 'Dibujo reanudado'
        return response

    def reiniciar_callback(self, request, response):
        # Vuelve al punto inicial y empieza el 7 otra vez
        self.objetivo = 0
        self.pausado = False
        response.success = True
        response.message = 'Dibujo reiniciado'
        return response

    def mover(self, lineal, angular):
        # En ROS 2 Jazzy el TurtleBot3 de Gazebo usa TwistStamped
        msg = TwistStamped()
        msg.twist.linear.x = lineal
        msg.twist.angular.z = angular
        self.publisher.publish(msg)


def main():
    rclpy.init()
    nodo = DrawNumber()
    try:
        rclpy.spin(nodo)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
