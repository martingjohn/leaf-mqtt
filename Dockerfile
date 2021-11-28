FROM $BUILD_FROM

ENV PYTHONUNBUFFERED 1

RUN apk add --no-cache \
        gcc \
        git \
        musl-dev 

WORKDIR /conf
COPY config.ini /conf/

WORKDIR /app
COPY requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN chmod +x leaf-mqtt.py

ENTRYPOINT ["python", "leaf-mqtt.py"]
