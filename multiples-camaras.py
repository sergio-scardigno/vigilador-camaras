import os
import cv2
import time
import signal
import sys
import logging
from ultralytics import YOLO
from dotenv import load_dotenv
import threading
from datetime import datetime
import requests

# Cargar las variables del archivo .env
load_dotenv()

# Configurar el logger
log_filename = f"log-{datetime.now().strftime('%Y-%m-%d')}.txt"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logging.info("Iniciando la detección de objetos en múltiples cámaras...")

# Obtener las variables de entorno
telegram_token = os.getenv('TELEGRAM_TOKEN')
telegram_chat_ids = os.getenv('TELEGRAM_CHAT_IDS').split(',')
camera_urls = os.getenv('CAMERA_URLS').split(',')  # Lista de URLs de cámaras
model_path = os.getenv('YOLO_MODEL', 'yolov8n.pt')  # Modelo YOLO

# Contador global de ciclos
cycle_count = 0
cycle_lock = threading.Lock()  # Para sincronizar el acceso al contador en entornos multihilo

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

# Manejar la interrupción Ctrl+C
def signal_handler(sig, frame):
    print("\nInterrupción detectada. Cerrando...")
    with cycle_lock:
        print(f"Total de ciclos procesados antes de salir: {cycle_count}")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Procesar cada cámara en un hilo separado
def process_camera(camera_url, camera_id):
    global cycle_count

    cap = None

    # Reconectar a la cámara en caso de desconexión
    def reconnect_camera(max_retries=5):
        nonlocal cap
        attempts = 0
        while attempts < max_retries:
            cap = cv2.VideoCapture(camera_url)
            cap.set(cv2.CAP_PROP_FPS, 10)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)

            if cap.isOpened():
                print(f"Cámara {camera_id}: Conexión exitosa.")
                return

            attempts += 1
            print(f"Cámara {camera_id}: Intento {attempts} de reconexión fallido.")
            time.sleep(1)

        print(f"Cámara {camera_id}: No se pudo conectar después de varios intentos.")
        sys.exit(1)

    reconnect_camera()

    # Cargar el modelo YOLO
    model = YOLO(model_path)

    # Variables de control
    frame_skip = 3
    frame_count = 0
    consecutive_frames_with_people = 0
    last_alert_time = 0

    try:
        while True:
            current_time = time.time()

            # Leer un fotograma
            ret, frame = cap.read()
            if not ret:
                print(f"Cámara {camera_id}: Reconectando...")
                cap.release()
                reconnect_camera()
                continue

            # Incrementar el contador de fotogramas
            frame_count += 1

            # Solo procesar 1 de cada 'frame_skip' fotogramas
            if frame_count % frame_skip != 0:
                continue

            # Procesar el fotograma con YOLO
            results = model(frame, verbose=False, conf=0.40)

            # Mostrar el frame (opcional)
            cv2.imshow(f"Cámara {camera_id}", frame)

            # Contadores para cada clase
            person_count = 0

            for result in results:
                if result.boxes is not None:
                    boxes = result.boxes
                    for box in boxes:
                        cls = int(box.cls)
                        if cls == 0:  # Clase "persona"
                            person_count += 1

            logging.info(f"Cámara {camera_id}: Personas detectadas: {person_count}")

            # Verificar si hay al menos 1 persona
            if person_count >= 1:
                consecutive_frames_with_people += 1
            else:
                consecutive_frames_with_people = 0

            # Enviar mensaje si se cumple la condición y respetar el intervalo entre alertas
            if consecutive_frames_with_people >= 100 and (current_time - last_alert_time > 5):
                image_filename = f"cam_{camera_id}_captura-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
                cv2.imwrite(image_filename, frame)
                logging.info(f"Cámara {camera_id}: Frame capturado y guardado como {image_filename}")
                send_telegram_message_with_photo(
                    f"🚨 Alerta desde cámara {camera_id}: Se han detectado personas durante más de 30 cuadros consecutivos.",
                    image_filename
                )
                consecutive_frames_with_people = 0
                last_alert_time = current_time

            # Incrementar el contador global de ciclos
            with cycle_lock:
                cycle_count += 1

            if cv2.waitKey(1) & 0xFF == ord('q'):
                print(f"Cámara {camera_id}: Cerrando la ventana...")
                break

    except KeyboardInterrupt:
        print(f"Cámara {camera_id}: Interrupción detectada. Cerrando...")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print(f"Cámara {camera_id}: Conexión finalizada.")

# Crear hilos para cada cámara
threads = []
for idx, camera_url in enumerate(camera_urls):
    thread = threading.Thread(target=process_camera, args=(camera_url, idx))
    threads.append(thread)
    thread.start()

# Esperar a que todos los hilos terminen
for thread in threads:
    thread.join()

