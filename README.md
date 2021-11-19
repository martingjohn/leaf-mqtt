# leaf-mqtt
Script that connects your Nissan Leaf to MQTT

There are a number of variables needed, the defaults stored in config.ini (below)

```
[get-leaf-info]
#username =
#password =
#mqtt_host =
#mqtt_username =
#mqtt_password =
mqtt_port = 1883
mqtt_control_topic = leaf/control
mqtt_status_topic = leaf/status
nissan_region_code = NE
api_update_interval_min = 10
```
Once built (docker build -t leaf-mqtt .) the container can be started as follows overriding the defaults in the start up command (username and password being the ones you use to log into the Nissan app)

```
docker run \
       --rm \
       -d \
       -e USERNAME="user@provider.com" \
       -e PASSWORD="secret_password" \
       -e MQTT_HOST="mqtt_host.local" \
       -e MQTT_PORT="1883" \
       -e MQTT_USERNAME="mqtt_user" \
       -e MQTT_PASSWORD='mqtt_pass' \
       -e MQTT_CONTROL_TOPIC="leaf/control" \
       -e MQTT_STATUS_TOPIC="leaf/status" \
       -e NISSAN_REGION_CODE='NE' \
       -e API_UPDATE_INTERVAL_MIN='30' \
       --name leaf-mqtt \
       leaf-mqtt
```
