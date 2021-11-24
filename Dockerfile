FROM $BUILD_FROM

ENV PYTHONUNBUFFERED 1

RUN apk add --no-cache \
        gcc \
        git \
        musl-dev 

RUN mkdir /conf
COPY config.ini /conf/

COPY . /app
WORKDIR /app
RUN chmod +x leaf-mqtt.py

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "leaf-mqtt.py"]
