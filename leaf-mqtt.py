#!/usr/bin/python

import pycarwings2
import time
from configparser import SafeConfigParser, NoOptionError
import logging
import sys
import pprint
import paho.mqtt.client as mqtt
import schedule
from datetime import datetime
import os

config_file = '/conf/config.ini'
config_settings = [
    'username',
    'password',
    'mqtt_host',
    'mqtt_port',
    'mqtt_username',
    'mqtt_password',
    'mqtt_control_topic',
    'mqtt_status_topic',
    'nissan_region_code',
    'api_update_interval_min'
]
settings = {}

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.info("Startup leaf-mqtt: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
config_file_path = config_file

# Get config from environment
for setting in config_settings:
    try:
        settings[setting] = os.environ[setting.upper()]
    except KeyError:
        logging.info("Unable to find setting " + setting.upper() + " in env")
        pass

# Get login details from 'config.ini' or environment
parser = SafeConfigParser()
if os.path.exists(config_file_path):
    logging.info("Loaded config file " + config_file_path)
    candidates = config_file_path
    parser.read(candidates)
    for setting in config_settings:
        if setting not in settings:
            try:
                settings[setting] = parser.get('get-leaf-info', setting)
            except NoOptionError:
                logging.error("Unable to find setting " + setting)
                exit(1)
else:
    logging.error("ERROR: Config file not found " + config_file_path)
    sys.exit(1)

# Check for MQTT cert


# Set variables (should be rewritten to use dict)
username = settings['username']
password = settings['password']
mqtt_host = settings['mqtt_host']
mqtt_port = 1883
mqtt_username = settings['mqtt_username']
mqtt_password = settings['mqtt_password']
mqtt_control_topic = settings['mqtt_control_topic']
mqtt_status_topic = settings['mqtt_status_topic']
nissan_region_code = settings['nissan_region_code']
api_update_interval_min = settings['api_update_interval_min']


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    logging.info("Connected to MQTT host " + mqtt_host + " with result code "+str(rc))
    logging.info("Suscribing to leaf control topic: " + mqtt_control_topic)
    client.subscribe(mqtt_control_topic + "/#")
    logging.info("Publishing to leaf status topic: " + mqtt_status_topic)
    client.publish(mqtt_status_topic, "MQTT connected")


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):

    logging.info(msg.topic+" "+str(msg.payload))

    control_subtopic = msg.topic.rsplit('/', 1)[1]
    control_message = msg.payload
    logging.info("control sub-topic: " + control_subtopic)
    logging.info("control message: " + control_message)

    # If climate control messaage is received mqtt_control_topic/climate
    if control_subtopic == 'climate':
        logging.info('Climate control command received: ' + control_message)

        if control_message == '1':
            climate_control(1)

        if control_message == '0':
            climate_control(0)

    # If climate control messaage is received on mqtt_control_topic/update
    if control_subtopic == 'update':
        logging.info('Update control command received: ' + control_message)
        if control_message == '1':
            leaf_info = get_leaf_update()
            time.sleep(10)
            mqtt_publish(leaf_info)


def mqtt_publish(leaf_info):
    logging.info("End update time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    logging.info("publishing to MQTT base status topic: " + mqtt_status_topic)
    utc_datetime = datetime.strptime(leaf_info.answer["BatteryStatusRecords"]["NotificationDateAndTime"], '%Y/%m/%d %H:%M')
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    client.publish(mqtt_status_topic + "/last_updated", (utc_datetime + offset).strftime("%d.%m %H:%M"))
    time.sleep(1)
    client.publish(mqtt_status_topic + "/battery_percent", leaf_info.battery_percent)
    time.sleep(1)
    client.publish(mqtt_status_topic + "/charging_status", leaf_info.charging_status)
    time.sleep(1)
    client.publish(mqtt_status_topic + "/charge_time", str(leaf_info.time_to_full_l2))
    time.sleep(1)

    # Added some extras
    client.publish(mqtt_status_topic + "/range_ac_on_km",leaf_info.cruising_range_ac_on_km)
    time.sleep(1)
    client.publish(mqtt_status_topic + "/range_ac_off_km",leaf_info.cruising_range_ac_off_km)
    time.sleep(1)
    off_m=round(float(leaf_info.cruising_range_ac_off_km)*0.621371)
    on_m=round(float(leaf_info.cruising_range_ac_on_km)*0.621371)
    client.publish(mqtt_status_topic + "/range_ac_on_miles",on_m)
    time.sleep(1)
    client.publish(mqtt_status_topic + "/range_ac_off_miles",off_m)
    time.sleep(1)

    if leaf_info.is_connected == True:
        client.publish(mqtt_status_topic + "/connected", "Yes")
    elif leaf_info.is_connected == False:
        client.publish(mqtt_status_topic + "/connected", "No")
    else:
        client.publish(mqtt_status_topic + "/connected", leaf_info.is_connected)


#
# Start MQTT
#
client = mqtt.Client("", True, None, mqtt.MQTTv31)

# Callback when MQTT is connected
client.on_connect = on_connect

# Callback when MQTT message is received
client.on_message = on_message

# Connect to MQTT
if 'mqtt_cert' in settings:
    client.tls_set(settings['mqtt_cert'])

client.username_pw_set(mqtt_username, mqtt_password)
client.connect(mqtt_host, mqtt_port, 60)
client.publish(mqtt_status_topic, "Connected to MQTT host " + mqtt_host)

# Non-blocking MQTT subscription loop
client.loop_start()


def climate_control(climate_control_instruction):
    logging.debug("login = %s , password = %s" % (username, password))
    logging.info("Prepare Session climate control update")
    s = pycarwings2.Session(username, password, "NE")
    logging.info("Login...")
    logging.info(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    l = s.get_leaf()

    if climate_control_instruction == 1:
        logging.info("Turning on climate control..wait 60s")
        result_key = l.start_climate_control()
        time.sleep(60)
        start_cc_result = l.get_start_climate_control_result(result_key)
        logging.info(start_cc_result)

    if climate_control_instruction == 0:
        logging.info("Turning off climate control..wait 60s")
        result_key = l.stop_climate_control()
        time.sleep(60)
        stop_cc_result = l.get_stop_climate_control_result(result_key)
        logging.info(stop_cc_result)


# Request update from car, use carefully: requires car GSM modem to powerup
def get_leaf_update():
    logging.debug("login = %s , password = %s" % (username, password))
    logging.info("Prepare Session get car update")
    s = pycarwings2.Session(username, password, "NE")
    logging.info("Login...")
    logging.info(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    try:
        l = s.get_leaf()
    except:
        logging.error("CarWings API error")
        return

    logging.info("Requesting update from car..wait 30s")
    try:
        result_key = l.request_update()
    except:
        logging.error("ERROR: no responce from car update")

    time.sleep(30)
    battery_status = l.get_status_from_update(result_key)

    while battery_status is None:
        logging.error("ERROR: no responce from car")
        time.sleep(10)
        battery_status = l.get_status_from_update(result_key)

    leaf_info = l.get_latest_battery_status()
    return (leaf_info)


# Get last updated data from Nissan server
def get_leaf_status():
    logging.debug("login = %s , password = %s" % ( username , password) )
    logging.info("Prepare Session")
    s = pycarwings2.Session(username, password, nissan_region_code)
    logging.info("Login...")
    logging.info("Start update time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    try:
        l = s.get_leaf()
    except:
        logging.error("CarWings API error")
        return

    logging.info("get_latest_battery_status")

    leaf_info = l.get_latest_battery_status()

    logging.info("date %s" % leaf_info.answer["BatteryStatusRecords"]["OperationDateAndTime"])
    logging.info("date %s" % leaf_info.answer["BatteryStatusRecords"]["NotificationDateAndTime"])
    logging.info("battery_capacity2 %s" % leaf_info.answer["BatteryStatusRecords"]["BatteryStatus"]["BatteryCapacity"])
    logging.info("battery_capacity %s" % leaf_info.battery_capacity)
    logging.info("charging_status %s" % leaf_info.charging_status)
    logging.info("battery_capacity %s" % leaf_info.battery_capacity)
    logging.info("battery_remaining_amount %s" % leaf_info.battery_remaining_amount)
    logging.info("charging_status %s" % leaf_info.charging_status)
    logging.info("is_charging %s" % leaf_info.is_charging)
    logging.info("is_quick_charging %s" % leaf_info.is_quick_charging)
    logging.info("plugin_state %s" % leaf_info.plugin_state)
    logging.info("is_connected %s" % leaf_info.is_connected)
    logging.info("is_connected_to_quick_charger %s" % leaf_info.is_connected_to_quick_charger)
    logging.info("time_to_full_trickle %s" % leaf_info.time_to_full_trickle)
    logging.info("time_to_full_l2 %s" % leaf_info.time_to_full_l2)
    logging.info("time_to_full_l2_6kw %s" % leaf_info.time_to_full_l2_6kw)
    logging.info("leaf_info.battery_percent %s" % leaf_info.battery_percent)

    # Added some extras
    logging.info("Range AC off (km) - %s" % leaf_info.cruising_range_ac_off_km)
    logging.info("Range AC on (km) - %s" % leaf_info.cruising_range_ac_on_km)
    off_m=round(float(leaf_info.cruising_range_ac_off_km)*0.621371)
    on_m=round(float(leaf_info.cruising_range_ac_on_km)*0.621371)
    logging.info("Range AC off (miles) - %s" % off_m)
    logging.info("Range AC on (miles) - %s" % on_m)


    # logging.info("getting climate update")
    # climate = l.get_latest_hvac_status()
    # pprint.pprint(climate)

    mqtt_publish(leaf_info)

    logging.info("End update time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logging.info("Schedule API update every " + api_update_interval_min + "min")
    return (leaf_info)


# Run initial get_status
get_leaf_status()

# Run schedule
logging.info("Schedule API update every " + api_update_interval_min + "min")
schedule.every(int(api_update_interval_min)).minutes.do(get_leaf_status)

while True:
    schedule.run_pending()
    time.sleep(1)
