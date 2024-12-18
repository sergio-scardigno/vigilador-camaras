# import os
# import cv2
# import time
# import socket
# import signal
# import sys
# import logging
# from ultralytics import YOLO
# from twilio.rest import Client
# from dotenv import load_dotenv

# # Cargar las variables del archivo .env
# load_dotenv()

# # Configurar el logger
# logging.basicConfig(
#     filename='log.txt',          # El archivo donde se guardarán los logs
#     level=logging.INFO,          # Nivel de log (puedes cambiarlo a DEBUG, ERROR, etc.)
#     format='%(asctime)s - %(message)s',  # Formato que incluye la hora
#     datefmt='%Y-%m-%d %H:%M:%S'   # Formato de la hora (Año-Mes-Día Hora:Minuto:Segundo)
# )

# logging.info("Iniciando la detección de objetos...")

# # Obtener las variables de entorno
# twilio_sid = os.getenv('TWILIO_SID')
# twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
# twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
# to_phone_number = os.getenv('TO_PHONE_NUMBER')
# dominio = os.getenv('DOMINIO')
# camera_url = os.getenv('CAMARA_URL')

# # Manejo de interrupción Ctrl + C
# def signal_handler(sig, frame):
#     print("\nInterrupción recibida. Cerrando el programa...")
#     cap.release()
#     sys.exit(0)

# signal.signal(signal.SIGINT, signal_handler)

# try:
#     direccion_ip = socket.gethostbyname(dominio)
#     print(f"La dirección IP para {dominio} es: {direccion_ip}")
# except socket.gaierror as e:
#     print(f"No se pudo resolver el dominio {dominio}: {e}")
#     exit()

# # Reconexión a la cámara IP
# def reconnect_camera():
#     while True:
#         cap = cv2.VideoCapture(camera_url)
#         cap.set(cv2.CAP_PROP_FPS, 10)
#         cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)

#         if cap.isOpened():
#             print("Conexión exitosa a la cámara.")
#             return cap
#         else:
#             print("No se pudo conectar a la cámara. Intentando nuevamente...")
#             time.sleep(1)

# cap = reconnect_camera()

# # Cargar el modelo YOLOv8 preentrenado
# model = YOLO('yolov8n.pt')  # Modelo ligero para tiempo real

# # Cliente Twilio
# client = Client(twilio_sid, twilio_auth_token)

# def send_sms_batch():
#     print("¡Enviando 1 mensaje SMS de alerta!")
#     for i in range(1):
#         message = client.messages.create(
#             body="Alerta: Se han detectado al menos 2 personas y 1 bicicleta en la zona monitoreada durante más de 5 segundos.",
#             from_=twilio_phone_number,
#             to=to_phone_number
#         )
#         print(f"Mensaje enviado con SID: {message.sid}")
#         time.sleep(1)

# # Centralización de tiempos
# TIME_SETTINGS = {
#     "analysis_interval": 0.5,
#     "detection_duration": 2,
#     "alert_interval": 5,
# }

# DETECTION_CLASSES = {
#     "person": 0,
#     "bicycle": 1,
#     "car": 2
# }

# start_detection_time = None
# last_analysis_time = 0
# last_alert_time = 0

# # Reducir la frecuencia de análisis
# frame_skip = 5  # Procesar 1 de cada 5 fotogramas
# frame_count = 0

# try:
#     while True:
#         current_time = time.time()

#         # Leer un fotograma
#         ret, frame = cap.read()
#         if not ret:
#             print("Reconectando...")
#             cap.release()
#             cap = reconnect_camera()
#             continue

#         # Incrementar el contador de fotogramas
#         frame_count += 1

#         # Solo procesar 1 de cada 'frame_skip' fotogramas
#         if frame_count % frame_skip != 0:
#             continue

#         # Procesar el fotograma con YOLO
#         results = model(frame, verbose=False, conf=0.40)

#         # Para ver el frame
#         #cv2.imshow("Vista de la Cámara", frame)
        
#         # Contadores para cada clase
#         person_count = 0
#         bicycle_count = 0
#         car_count = 0

#         for result in results:
#             if result.boxes is not None:
#                 boxes = result.boxes
#                 for box in boxes:
#                     cls = int(box.cls)
#                     confidence = box.conf.item()
#                     x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

#                     if cls not in DETECTION_CLASSES.values():
#                         continue

#                     if cls == DETECTION_CLASSES["person"]:
#                         person_count += 1
#                         cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
#                         cv2.putText(frame, f"Person {confidence:.2f}", (x1, y1 - 10),
#                                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
#                     elif cls == DETECTION_CLASSES["bicycle"]:
#                         bicycle_count += 1
#                         cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
#                         cv2.putText(frame, f"Bicycle {confidence:.2f}", (x1, y1 - 10),
#                                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
#                     elif cls == DETECTION_CLASSES["car"]:
#                         car_count += 1
#                         cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
#                         cv2.putText(frame, f"Car {confidence:.2f}", (x1, y1 - 10),
#                                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

#         logging.info(f"Personas: {person_count}, Bicicletas: {bicycle_count}, Autos: {car_count}")
        
#         #print(f"Personas: {person_count}, Bicicletas: {bicycle_count}, Autos: {car_count}")

#         if person_count >= 2 and bicycle_count:
#             if not start_detection_time:
#                 start_detection_time = current_time

#             if current_time - start_detection_time >= TIME_SETTINGS["detection_duration"]:
#                 if current_time - last_alert_time >= TIME_SETTINGS["alert_interval"]:
#                     send_sms_batch()
#                     last_alert_time = current_time
#         else:
#             start_detection_time = None

#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             print("Cerrando la ventana...")
#             break

# except KeyboardInterrupt:
#     print("\nInterrupción detectada. Cerrando...")
# finally:
#     cap.release()
#     cv2.destroyAllWindows()
#     print("Conexión finalizada.")

import os
import cv2
import time
import socket
import signal
import sys
import logging
from ultralytics import YOLO
from dotenv import load_dotenv
import psutil  # Para detectar instancias
from datetime import datetime  # Para manejar fechas
import requests  # Para interactuar con la API de Telegram

# Verificar si ya hay una instancia en ejecución
def is_already_running():
    current_pid = os.getpid()
    current_script = os.path.basename(__file__)
    for process in psutil.process_iter(['pid', 'cmdline']):
        cmdline = process.info['cmdline']
        if cmdline and process.info['pid'] != current_pid and current_script in cmdline:
            return True

    return False

if is_already_running():
    print("El programa ya está en ejecución. Saliendo...")
    sys.exit()

# Cargar las variables del archivo .env
load_dotenv()

# Configurar el logger con la fecha actual
log_filename = f"log-{datetime.now().strftime('%Y-%m-%d')}.txt"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logging.info("Iniciando la detección de objetos...")

# Obtener las variables de entorno
telegram_token = os.getenv('TELEGRAM_TOKEN')
telegram_chat_ids = os.getenv('TELEGRAM_CHAT_IDS').split(',')
dominio = os.getenv('DOMINIO')
camera_url = os.getenv('CAMARA_URL')

# Manejo de interrupción Ctrl + C
def signal_handler(sig, frame):
    print("\nInterrupción recibida. Cerrando el programa...")
    cap.release()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

try:
    direccion_ip = socket.gethostbyname(dominio)
    print(f"La dirección IP para {dominio} es: {direccion_ip}")
except socket.gaierror as e:
    print(f"No se pudo resolver el dominio {dominio}: {e}")
    exit()

# Reconexión a la cámara IP
def reconnect_camera(max_retries=5):
    attempts = 0
    while attempts < max_retries:
        cap = cv2.VideoCapture(camera_url)
        cap.set(cv2.CAP_PROP_FPS, 10)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)

        if cap.isOpened():
            print("Conexión exitosa a la cámara.")
            return cap

        attempts += 1
        print(f"Intento {attempts} de reconexión fallido. Reintentando...")
        time.sleep(1)

    print("No se pudo conectar a la cámara después de varios intentos.")
    sys.exit(1)

cap = reconnect_camera()

# Cargar el modelo YOLOv8 preentrenado
model = YOLO('yolov8n.pt')  # Modelo ligero para tiempo real

# Función para enviar mensajes de Telegram con una foto adjunta
def send_telegram_message_with_photo(text, image_path):
    print("Enviando mensaje de alerta con foto por Telegram...")
    for chat_id in telegram_chat_ids:
        try:
            url = f"https://api.telegram.org/bot{telegram_token}/sendPhoto"
            with open(image_path, 'rb') as image_file:
                payload = {
                    "chat_id": chat_id.strip(),
                    "caption": text
                }
                files = {
                    "photo": image_file
                }
                response = requests.post(url, data=payload, files=files)
                if response.status_code == 200:
                    print(f"Mensaje con foto enviado al chat ID {chat_id.strip()}")
                else:
                    print(f"Error al enviar el mensaje con foto al chat ID {chat_id.strip()}: {response.text}")
                    logging.error(f"Error al enviar el mensaje con foto al chat ID {chat_id.strip()}: {response.text}")
        except Exception as e:
            logging.error(f"Excepción al enviar mensaje con foto a Telegram: {e}")
            print(f"Error al enviar mensaje con foto a Telegram: {e}")

# Centralización de tiempos
TIME_SETTINGS = {
    "analysis_interval": 0.5,
    "detection_duration": 1,
    "alert_interval": 5,
}

DETECTION_CLASSES = {
    "person": 0,
}

start_detection_time = None
last_analysis_time = 0
last_alert_time = 0

# Reducir la frecuencia de análisis
frame_skip = 3  # Procesar 1 de cada 3 fotogramas
frame_count = 0

# Contador de cuadros consecutivos con al menos 1 persona
consecutive_frames_with_people = 0

try:
    while True:
        current_time = time.time()

        # Leer un fotograma
        ret, frame = cap.read()
        if not ret:
            print("Reconectando...")
            cap.release()
            cap = reconnect_camera()
            continue

        # Incrementar el contador de fotogramas
        frame_count += 1

        # Solo procesar 1 de cada 'frame_skip' fotogramas
        if frame_count % frame_skip != 0:
            continue

        # Procesar el fotograma con YOLO
        results = model(frame, verbose=False, conf=0.40)

        # Para ver el frame
        cv2.imshow("Vista de la Cámara", frame)

        # Contadores para cada clase
        person_count = 0

        for result in results:
            if result.boxes is not None:
                boxes = result.boxes
                for box in boxes:
                    cls = int(box.cls)
                    if cls == DETECTION_CLASSES["person"]:
                        person_count += 1

        logging.info(f"Personas: {person_count}")

        # Verificar si hay al menos 1 persona
        if person_count >= 1:
            consecutive_frames_with_people += 1
        else:
            consecutive_frames_with_people = 0

        # Enviar mensaje si se cumple la condición y respetar el intervalo entre alertas
        if consecutive_frames_with_people >= 100 and (current_time - last_alert_time > TIME_SETTINGS["alert_interval"]):
            image_filename = f"captura-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
            cv2.imwrite(image_filename, frame)
            logging.info(f"Frame capturado y guardado como {image_filename}")
            send_telegram_message_with_photo(
                "🚨 Alerta: Se han detectado personas en la zona monitoreada durante más de 30 cuadros consecutivos.",
                image_filename
            )
            consecutive_frames_with_people = 0
            last_alert_time = current_time

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Cerrando la ventana...")
            break

except KeyboardInterrupt:
    print("\nInterrupción detectada. Cerrando...")
finally:
    cap.release()
    cv2.destroyAllWindows()
    print("Conexión finalizada.")
