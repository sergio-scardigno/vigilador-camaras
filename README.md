# Vigilador de Cámaras - Sistema de Detección y Alerta

## Descripción

El proyecto **Vigilador de Cámaras** utiliza un modelo de detección de objetos basado en **YOLOv8** para analizar los flujos de video provenientes de una cámara IP. La aplicación está diseñada para detectar personas y bicicletas en la imagen y enviar una alerta SMS cuando se detecta la presencia de al menos 2 personas y 1 bicicleta en la zona monitoreada.

**Funcionalidades:**

-   Conexión a una cámara IP para capturar video en tiempo real.
-   Análisis del flujo de video utilizando el modelo YOLOv8.
-   Detección de personas y bicicletas.
-   Envío de alertas SMS a través de la API de Twilio cuando se cumplen las condiciones de detección.

## Requisitos

Antes de ejecutar el proyecto, asegúrate de que tu entorno tenga las siguientes dependencias instaladas:

-   **Python 3.x**
-   **pip** (gestor de paquetes para Python)
-   **OpenCV** (para capturar y procesar el video)
-   **YOLOv8** (modelo de detección de objetos)
-   **Twilio** (para el envío de mensajes SMS)

## Instalación

### 1. Clona el repositorio:

```bash

git clone https://github.com/tu_usuario/vigilador-camaras.git
cd vigilador-camaras

```

## 2. Crea y activa un entorno virtual (opcional pero recomendado):

```bash
python3 -m venv venv
source venv/bin/activate  # En Linux o WSL

.\venv\Scripts\Activate

```

### 3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

### 4. Configura las variables de entorno

El archivo .env debe contener las siguientes variables de entorno:

```bash
TWILIO_SID=<tu_twilio_sid>
TWILIO_AUTH_TOKEN=<tu_twilio_auth_token>
TWILIO_PHONE_NUMBER=<tu_numero_twilio>
TO_PHONE_NUMBER=<numero_destino_alertas>
DOMINIO=<dominio_camara_ip>
CAMARA_URL=<url_camara_ip>
```

Para obtener tus credenciales de Twilio, regístrate en Twilio.

### 5. Ejecuta la aplicación

Inicia la aplicación con el siguiente comando:

```bash
python video.py
```

### 6. Generar el ejecutable (opcional)

Si deseas generar un ejecutable para Linux, puedes usar PyInstaller:

```bash
pip install pyinstaller
```

```bash
pyinstaller --onefile --name video video.py


```

##### Si estas en Windows y quieres crear un ejecutable para Linux deberas usar WSL

```bash
wsl --install
```
