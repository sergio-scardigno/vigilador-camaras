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
logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')


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

# Función para manejar la interrupción del programa con Ctrl + C
def signal_handler(sig, frame):
    print("\nInterrupción recibida. Cerrando el programa...")
    cap.release()
    sys.exit(0)

# Registrar el manejador de señales para Ctrl + C
signal.signal(signal.SIGINT, signal_handler)

# Obtener la dirección IP del dominio
dominio = "calle56numero1781.dyndns.org"

try:
    # Obtener la dirección IP
    direccion_ip = socket.gethostbyname(dominio)
    print(f"La dirección IP para {dominio} es: {direccion_ip}")
except socket.gaierror as e:
    print(f"No se pudo resolver el dominio {dominio}: {e}")
    exit()

# URL de la cámara IP (modifica con tus credenciales y dirección)
camera_url = "rtsp://segundob:perro1017@calle56numero1781.dyndns.org/Streaming/Channels/101"

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
model = YOLO('yolov8n.pt')  # Modelo ligero para tiempo real

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

# Variables para controlar el tiempo de detección
start_detection_time = None  # Tiempo inicial de detección
detection_duration = 5       # Duración mínima requerida para enviar alertas (en segundos)
last_alert_time = 0          # Tiempo del último envío de mensajes
alert_interval = 120         # Intervalo de espera entre lotes de mensajes (en segundos)


try:
    while True:
        start_time = time.time()  # Registrar tiempo de inicio de la iteración

        try:
            ret, frame = cap.read()
            if not ret:
                raise ValueError("No se pudo leer el fotograma.")
        except cv2.error as e:
            print(f"Error de OpenCV: {e}")
            cap.release()
            cap = reconnect_camera()
            continue
        except Exception as e:
            print(f"Error al leer el fotograma: {e}")
            cap.release()
            cap = reconnect_camera()
            continue

        # Procesar el fotograma con el modelo YOLO
        results = model(frame, verbose=False)

        # Contar cuántas personas y bicicletas son detectadas
        person_count = 0
        bicycle_count = 0
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls[0])  # Clase de la detección
                confidence = box.conf[0]  # Confianza de la detección
                x1, y1, x2, y2 = map(int, box.xyxy[0])  # Coordenadas del cuadro delimitador

                if cls == 0:  # Detectar personas
                    person_count += 1
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                elif cls == 1:  # Detectar bicicletas
                    bicycle_count += 1
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

        # Logging de resultados
        logging.info(f"Personas detectadas: {person_count}, Bicicletas detectadas: {bicycle_count}")

        # Verificar si se cumplen las condiciones de detección
        current_time = time.time()
        if person_count >= 2 and bicycle_count >= 1:
            if start_detection_time is None:
                start_detection_time = current_time
            elif current_time - start_detection_time >= detection_duration:
                if current_time - last_alert_time >= alert_interval:
                    send_sms_batch()
                    last_alert_time = current_time
        else:
            start_detection_time = None

        # Ajustar el retraso dinámico si es necesario
        elapsed_time = time.time() - start_time
        delay = max(0, 0.1 - elapsed_time)
        time.sleep(delay)

except KeyboardInterrupt:
    print("\nInterrupción del programa detectada. Cerrando la conexión...")
finally:
    cap.release()
    print("Conexión finalizada.")