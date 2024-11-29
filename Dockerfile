FROM python:3.9-slim

# Instalar dependencias gráficas para OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar el código al contenedor
COPY . /app

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "video.py"]

