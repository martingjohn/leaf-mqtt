# leaf-mqtt
Script that connects your Nissan Leaf to MQTT

There are a number of variables needed, the defaults stored in config.ini (below)
homeassisant = 1 - register devices on Home Assistant's discovery topic
homeassisant = 0 - don't register devices on Home Assistant's discovery topic

ha_name - only relevant when registering on Home Assistant, this is the what the entity name is called. If not set it will default to the title case of the mqtt_status_topic's first part, e.g. if mqtt_status_topic = leaf/status it will default to Leaf

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
homeassistant = 1
```
Once built (docker build -t leaf-mqtt .) the container can be started as follows overriding the defaults in the start up command (username and password being the ones you use to log into the Nissan app)

```
docker run \
       --rm \
       -d \
       -e USERNAME="user@provider.com" \
       -e PASSWORD="secret_password" \
       -e MQTT_HOST="mqtt_host.local" \
       -e MQTT_PORT=1883 \
       -e MQTT_USERNAME="mqtt_user" \
       -e MQTT_PASSWORD='mqtt_pass' \
       -e MQTT_CONTROL_TOPIC="leaf/control" \
       -e MQTT_STATUS_TOPIC="leaf/status" \
       -e NISSAN_REGION_CODE="NE" \
       -e API_UPDATE_INTERVAL_MIN=30 \
       -e HOMEASSISTANT=1 \
       -e HA_NAME="My Leaf" \
       --name leaf-mqtt \
       leaf-mqtt
```
