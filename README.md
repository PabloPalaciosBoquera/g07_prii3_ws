# ROS 2 Turtlesim - Grupo 07

Proyecto desarrollado por el **Grupo 07** para el **Sprint 1 de Proyectos III**.

El proyecto implementa un paquete de ROS 2 que controla de forma autónoma una tortuga de `turtlesim` para dibujar el número **7**.

Además del movimiento autónomo, el nodo dispone de tres servicios ROS 2 que permiten:

- Detener el dibujo.
- Reanudar el dibujo.
- Reiniciar el dibujo.

---

## 1. Entorno de desarrollo

El proyecto ha sido desarrollado y probado utilizando:

- Ubuntu 24.04
- ROS 2 Jazzy
- Python 3
- `rclpy`
- `geometry_msgs`
- `std_srvs`
- `turtlesim`

> El enunciado original del Sprint 1 especifica Ubuntu 22.04 y ROS 2 Humble. Esta versión del proyecto ha sido desarrollada y verificada utilizando Ubuntu 24.04 y ROS 2 Jazzy.

---

## 2. Estructura del workspace

El workspace utilizado es:

```text
g07_prii3_ws
```

El paquete ROS 2 es:

```text
g07_prii3_turtlesim
```

La estructura principal del proyecto es:

```text
g07_prii3_ws/
│
├── src/
│   └── g07_prii3_turtlesim/
│       │
│       ├── g07_prii3_turtlesim/
│       │   ├── __init__.py
│       │   └── dibujar_7.py
│       │
│       ├── launch/
│       │   └── dibujar_7.launch.py
│       │
│       ├── resource/
│       │   └── g07_prii3_turtlesim
│       │
│       ├── test/
│       │
│       ├── package.xml
│       ├── setup.cfg
│       └── setup.py
│
├── .gitignore
└── README.md
```

Los directorios `build/`, `install/` y `log/` son generados automáticamente durante la compilación y no se almacenan en el repositorio.

---

## 3. Funcionamiento

El nodo principal se encuentra en:

```text
src/g07_prii3_turtlesim/g07_prii3_turtlesim/dibujar_7.py
```

El nodo controla el movimiento de `turtle1` de forma autónoma para dibujar el número **7**.

La trayectoria predefinida es:

```text
(2,10)
   ↓
(10,10)
   ↓
(7,6)
   ↓
(5,6)
   ↓
(9,6)
   ↓
(7,6)
   ↓
(4,2)
```

Expresada de forma compacta:

```text
(2,10) → (10,10) → (7,6) → (5,6) → (9,6) → (7,6) → (4,2)
```

El movimiento se realiza mediante mensajes ROS 2 enviados a `turtlesim`.

Una vez alcanzado el último punto, el nodo detiene la tortuga y finaliza el dibujo.

---

## 4. Descargar el proyecto

Clonar el repositorio:

```bash
git clone https://github.com/PabloPalaciosBoquera/g07_prii3_ws.git
```

Acceder al workspace:

```bash
cd g07_prii3_ws
```

> La URL anterior debe sustituirse por la URL definitiva de este repositorio de GitHub.

---

## 5. Compilar el proyecto

### ROS 2 Jazzy con Bash

Cargar el entorno de ROS 2:

```bash
source /opt/ros/jazzy/setup.bash
```

Desde la raíz del workspace, compilar:

```bash
colcon build --symlink-install
```

Después de la compilación, cargar el workspace:

```bash
source install/setup.bash
```

### ROS 2 Jazzy con Zsh

Si se utiliza `zsh`:

```bash
source /opt/ros/jazzy/setup.zsh
colcon build --symlink-install
source install/setup.zsh
```

---

## 6. Ejecutar el proyecto

Con ROS 2 y el workspace cargados, ejecutar:

```bash
ros2 launch g07_prii3_turtlesim dibujar_7.launch.py
```

El fichero `launch` inicia automáticamente:

1. El nodo de `turtlesim`.
2. El nodo `dibujar_7`.

La tortuga se posicionará automáticamente y comenzará a dibujar el número 7.

---

## 7. Servicios ROS 2

El nodo implementa tres servicios utilizando:

```text
std_srvs/srv/Trigger
```

### Detener el dibujo

```bash
ros2 service call /detener_dibujo std_srvs/srv/Trigger "{}"
```

Detiene temporalmente el movimiento de la tortuga.

### Reanudar el dibujo

```bash
ros2 service call /reanudar_dibujo std_srvs/srv/Trigger "{}"
```

Continúa el dibujo desde el estado en el que se había detenido.

### Reiniciar el dibujo

```bash
ros2 service call /reiniciar_dibujo std_srvs/srv/Trigger "{}"
```

Reinicia el proceso de dibujo del número 7.

Los servicios disponibles también se pueden consultar mediante:

```bash
ros2 service list
```

---

## 8. Ejecutable ROS 2

El ejecutable del paquete está registrado en `setup.py` como:

```text
dibujar_7
```

Por tanto, el nodo también puede ejecutarse directamente mediante:

```bash
ros2 run g07_prii3_turtlesim dibujar_7
```

Para el funcionamiento completo del proyecto se recomienda utilizar el fichero `launch`:

```bash
ros2 launch g07_prii3_turtlesim dibujar_7.launch.py
```

---

## 9. Comprobación del paquete

Para comprobar que ROS 2 reconoce correctamente el paquete:

```bash
ros2 pkg list | grep g07_prii3_turtlesim
```

Para comprobar los ejecutables registrados:

```bash
ros2 pkg executables g07_prii3_turtlesim
```

Deberá aparecer:

```text
g07_prii3_turtlesim dibujar_7
```

---

## 10. Compilación desde cero

Para realizar una compilación completamente limpia:

```bash
rm -rf build install log
```

Cargar ROS 2:

```bash
source /opt/ros/jazzy/setup.bash
```

Compilar:

```bash
colcon build --symlink-install
```

Cargar el workspace:

```bash
source install/setup.bash
```

Y ejecutar:

```bash
ros2 launch g07_prii3_turtlesim dibujar_7.launch.py
```

---

## 11. Dependencias ROS 2

Las principales dependencias declaradas en `package.xml` son:

```text
rclpy
geometry_msgs
std_srvs
turtlesim
```

El paquete utiliza el sistema de construcción:

```text
ament_python
```

---

## 12. Resumen del proyecto

| Elemento | Nombre |
|---|---|
| Grupo | 07 |
| Workspace | `g07_prii3_ws` |
| Paquete | `g07_prii3_turtlesim` |
| Nodo principal | `dibujar_7` |
| Fichero Python | `dibujar_7.py` |
| Launch | `dibujar_7.launch.py` |
| Servicio detener | `/detener_dibujo` |
| Servicio reanudar | `/reanudar_dibujo` |
| Servicio reiniciar | `/reiniciar_dibujo` |
| Build type | `ament_python` |
| Licencia | Apache-2.0 |

---

## 13. Licencia

Este proyecto utiliza la licencia:

```text
Apache-2.0
```
