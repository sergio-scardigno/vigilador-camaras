import os
import cv2
import time
import socket
import signal
import sys
import logging
from ultralytics import YOLO
from twilio.rest import Client
import threading
import logging
from dotenv import load_dotenv

# Cargar las variables del archivo .env
load_dotenv()


# Configurar el logger
logging.basicConfig(filename='C:\\Users\\sergi\\Proyectos\\python\\vigilador-camaras\\dist\\log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')


# Configurar el logger para guardar los logs en un archivo y mostrar la hora
logging.basicConfig(
    filename='log.txt',          # El archivo donde se guardarán los logs
    level=logging.INFO,          # Nivel de log (puedes cambiarlo a DEBUG, ERROR, etc.)
    format='%(asctime)s - %(message)s',  # Formato que incluye la hora
    datefmt='%Y-%m-%d %H:%M:%S'   # Formato de la hora (Año-Mes-Día Hora:Minuto:Segundo)
)

# Ahora, en lugar de usar print(), usa logging
logging.info("Iniciando la detección de objetos...")

# Obtener las variables de entorno
twilio_sid = os.getenv('TWILIO_SID')
twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
to_phone_number = os.getenv('TO_PHONE_NUMBER')

# Obtener la dirección IP del dominio
dominio = os.getenv('DOMINIO')

# URL de la cámara IP (modifica con tus credenciales y dirección)
camera_url = os.getenv('CAMARA_URL')


# Función para manejar la interrupción del programa con Ctrl + C
def signal_handler(sig, frame):
    print("\nInterrupción recibida. Cerrando el programa...")
    cap.release()
    sys.exit(0)

# Registrar el manejador de señales para Ctrl + C
signal.signal(signal.SIGINT, signal_handler)


try:
    # Obtener la dirección IP
    direccion_ip = socket.gethostbyname(dominio)
    print(f"La dirección IP para {dominio} es: {direccion_ip}")
except socket.gaierror as e:
    print(f"No se pudo resolver el dominio {dominio}: {e}")
    exit()

# Función para intentar reconectar a la cámara IP
def reconnect_camera():
    while True:
        cap = cv2.VideoCapture(camera_url)
        cap.set(cv2.CAP_PROP_FPS, 10)  # Intenta limitar a 10 FPS (si la cámara lo permite)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)  # Ajusta el tamaño del búfer
        #cap.set(cv2.CAP_PROP_TIMEOUT, 5000)  # Tiempo de espera en milisegundos

        if cap.isOpened():
            print("Conexión exitosa a la cámara.")
            return cap
        else:
            print("No se pudo conectar a la cámara. Intentando nuevamente...")
            time.sleep(1)  # Espera 5 segundos antes de intentar reconectar

# Intentar conectar a la cámara
cap = reconnect_camera()

# Cargar el modelo YOLOv8 preentrenado
model = YOLO('yolov8m.pt')  # Modelo ligero para tiempo real

# Crear el cliente de Twilio
client = Client(twilio_sid, twilio_auth_token)

# Función para enviar un lote de 5 mensajes SMS usando Twilio
def send_sms_batch():
    print("¡Enviando 5 mensajes SMS de alerta!")
    for i in range(5):
        message = client.messages.create(
            body="Alerta: Se han detectado al menos 2 personas y 1 bicicleta en la zona monitoreada durante más de 5 segundos.",
            from_=twilio_phone_number,
            to=to_phone_number
        )
        print(f"Mensaje {i + 1} enviado con SID: {message.sid}")
        time.sleep(1)  # Pausa breve entre mensajes



# Centralización de tiempos
TIME_SETTINGS = {
    "analysis_interval": 5,        # Intervalo entre análisis de fotogramas (segundos)
    "detection_duration": 2,       # Duración mínima para enviar alertas (segundos)
    "alert_interval": 120,         # Intervalo entre lotes de alertas SMS (segundos)
    "sms_batch_delay": 1           # Pausa entre mensajes SMS en el lote (segundos)
}

# Detección de clases (COCO)
DETECTION_CLASSES = {
    "person": 0,
    "bicycle": 1,
    "car": 2  # Clase para autos
}

# Variables para controlar el tiempo
start_detection_time = None
last_analysis_time = 0
last_alert_time = 0

try:
    while True:
        current_time = time.time()

        # Analizar solo si ha pasado el intervalo especificado
        if current_time - last_analysis_time >= TIME_SETTINGS["analysis_interval"]:
            try:
                # Leer un fotograma
                ret, frame = cap.read()
                if not ret:
                    raise ValueError("No se pudo leer el fotograma.")
            except Exception as e:
                print(f"Error al leer el fotograma: {e}")
                cap.release()
                cap = reconnect_camera()
                continue

            # Procesar el fotograma con YOLO
            results = model(frame, verbose=False, conf=0.40)

            cv2.imshow("Vista de la Cámara", frame)

            # Contadores para cada clase
            person_count = 0
            bicycle_count = 0
            car_count = 0

            # Iterar sobre las detecciones
            for result in results:
                if result.boxes is not None:
                    boxes = result.boxes  # Todas las detecciones
                    for box in boxes:
                        cls = int(box.cls)  # Clase detectada
                        confidence = box.conf.item()  # Confianza de la detección
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())  # Coordenadas del cuadro delimitador

                        # Filtrar clases no deseadas
                        if cls not in DETECTION_CLASSES.values():
                            continue  # Ignorar clases no deseadas

                        # Dibujar rectángulos en el fotograma según la clase
                        if cls == DETECTION_CLASSES["person"]:  # Clase "persona"
                            person_count += 1
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Verde para personas
                            cv2.putText(frame, f"Person {confidence:.2f}", (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        elif cls == DETECTION_CLASSES["bicycle"]:  # Clase "bicicleta"
                            bicycle_count += 1
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)  # Azul para bicicletas
                            cv2.putText(frame, f"Bicycle {confidence:.2f}", (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                        elif cls == DETECTION_CLASSES["car"]:  # Clase "auto"
                            car_count += 1
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)  # Rojo para autos
                            cv2.putText(frame, f"Car {confidence:.2f}", (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            # Logging de resultados
            logging.info(f"Personas: {person_count}, Bicicletas: {bicycle_count}, Autos: {car_count}")
            print(f"Personas: {person_count}, Bicicletas: {bicycle_count}, Autos: {car_count}")

            # Lógica de detección para activar alertas
            if person_count >= 2 and bicycle_count:
                if not start_detection_time:
                    start_detection_time = current_time  # Inicia el tiempo de detección

                # Verificar si se cumple la duración mínima
                if current_time - start_detection_time >= TIME_SETTINGS["detection_duration"]:
                    if current_time - last_alert_time >= TIME_SETTINGS["alert_interval"]:
                        send_sms_batch()
                        last_alert_time = current_time  # Actualizar tiempo de última alerta
            else:
                start_detection_time = None  # Reiniciar si no se cumple la condición

            # Actualizar el tiempo del último análisis
            last_analysis_time = current_time

        # Mostrar el fotograma para monitoreo en tiempo real (opcional)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Cerrando la ventana...")
            break

except KeyboardInterrupt:
    print("\nInterrupción detectada. Cerrando...")
finally:
    cap.release()
    cv2.destroyAllWindows()
    print("Conexión finalizada.")
