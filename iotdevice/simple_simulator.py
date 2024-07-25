import json
import os
from sqlite3 import Timestamp
import subprocess
import time
import random

# copy uuid from Env var

DOCKER_ID_FILE = "/opt/iotdevice/DOCKER_ID"
if os.path.isfile(DOCKER_ID_FILE):
    with open(DOCKER_ID_FILE, "r") as f:
        think_id = f.read().strip()
        # Set the DOCKER_ID environment variable
        os.environ["DOCKER_ID"] = think_id
        print("Docker ID Found")
else:
    print("DOCKER_ID file not found::" + os.environ["DOCKER_ID"])


DOCKER_ID = os.environ["DOCKER_ID"]
ENDPOINT = os.environ["ENDPOINT"]
print(f"The DOCKER_ID is FPC-device-{DOCKER_ID}")
topic = f"dt/topic_base/topic/FPC-device-{DOCKER_ID}"
topic_ac = f"dt/topic_base/topic/FPC-device-{DOCKER_ID}"
topic_alarm = f"dt/topic_base/topic/FPC-device-{DOCKER_ID}"
topic_battery = f"dt/topic_base/topic/FPC-device-{DOCKER_ID}"
topic_env = f"dt/topic_base/topic/FPC-device-{DOCKER_ID}"
print(f"{topic}")
print(f"publishing to {ENDPOINT}")

tenant_names = ["Robi", "BL", "GP", "Airtel"]


def get_random_float(min, max):
    return round(random.uniform(min, max), 2)


def get_random_int(min, max):
    return random.randint(min, max)


def get_random_boolean():
    return random.randint(0, 1)


# Publish to the same topic in a loop forever
loopcount = 0
while True:

    persist_path = "/opt/iotdevice/persist/"

    cert_file_name = os.path.join(persist_path, "FPC-device-{}.certificate.pem").format(
        DOCKER_ID
    )
    key_file_name = os.path.join(persist_path, "FPC-device-{}.private.key").format(
        DOCKER_ID
    )

    # Tenant Data
    simulation_message = {
        "device_id": "FPC-device-" + DOCKER_ID,
        "tenant_name": tenant_names[get_random_int(0, len(tenant_names) - 1)],
        "dc_voltage": get_random_float(45.19999695, 54.19999695),
        "tenant_load": get_random_float(50.1, 70.1),
        "dc_power": get_random_float(1.5, 3.00),
        "cumulative_dc_energy": get_random_float(24.35000038, 26.35000038),
    }

    payload = json.dumps(simulation_message)

    print(simulation_message)

    cmd = f"mosquitto_pub --cafile rootcert.pem --cert {cert_file_name} --key {key_file_name} -h {ENDPOINT} -p 8883 -q 1 -t {topic} -I anyclientID --tls-version tlsv1.2 -m '{payload}' -d"
    print(cmd)
    pub = subprocess.getoutput(cmd)
    print(pub)

    # Ac _ Meter Data
    ac_message = {
        "device_id": "FPC-device-" + DOCKER_ID,
        "ac_source_name": 1,
        "voltage_phase_a": get_random_float(210.9, 235.0),
        "voltage_phase_b": get_random_float(210.9, 235.0),
        "voltage_phase_c": get_random_float(210.9, 235.0),
        "current_phase_a": get_random_float(10.00, 12.00),
        "current_phase_b": get_random_float(10.00, 12.00),
        "current_phase_c": get_random_float(10.00, 12.00),
        "frequency": get_random_float(49.7, 50.0),
        "power_factor": get_random_float(49.7, 50.0),
        "ac_cumulative_energy": get_random_float(0.555, 5.555),
        "ac_power": get_random_float(2.0, 10.0),
    }

    payload_ac = json.dumps(ac_message)

    cmd2 = f"mosquitto_pub --cafile rootcert.pem --cert {cert_file_name} --key {key_file_name} -h {ENDPOINT} -p 8883 -q 1 -t {topic_ac} -I anyclientID --tls-version tlsv1.2 -m '{payload_ac}' -d"
    pub2 = subprocess.getoutput(cmd2)
    print(pub2)

    # Alarms Data
    alarm_message = {
        "device_id": "FPC-device-" + DOCKER_ID,
        "mains_fail": get_random_boolean(),
        "dc_low_voltage": get_random_boolean(),
        "module_fault": get_random_boolean(),
        "llvd_fail": get_random_boolean(),
        "smoke_alarm": get_random_boolean(),
        "fan_fault": get_random_boolean(),
        "high_temperature_alarm": get_random_boolean(),
        "door_open_alarm": get_random_boolean(),
        "security_breach": get_random_boolean(),
    }

    payload_alarm = json.dumps(alarm_message)

    cmd3 = f"mosquitto_pub --cafile rootcert.pem --cert {cert_file_name} --key {key_file_name} -h {ENDPOINT} -p 8883 -q 1 -t {topic_alarm} -I anyclientID --tls-version tlsv1.2 -m '{payload_alarm}' -d"
    pub3 = subprocess.getoutput(cmd3)
    print(pub3)

    # Battery Data
    battery_message = {
        "device_id": "FPC-device-" + DOCKER_ID,
        "battery_number": str(random.randint(1, 4)),
        "current": get_random_float(20, 80),
        "voltage_of_pack": get_random_float(44, 52),
        "soc": random.randint(20, 100),
        "soh": random.randint(80, 100),
        "cell_voltage_01": get_random_float(3.2, 3.6),
        "cell_voltage_02": get_random_float(3.2, 3.6),
        "cell_voltage_03": get_random_float(3.2, 3.6),
        "cell_voltage_04": get_random_float(3.2, 3.6),
        "cell_voltage_05": get_random_float(3.2, 3.6),
        "cell_voltage_06": get_random_float(3.2, 3.6),
        "cell_voltage_07": get_random_float(3.2, 3.6),
        "cell_voltage_08": get_random_float(3.2, 3.6),
        "cell_voltage_09": get_random_float(3.2, 3.6),
        "cell_voltage_10": get_random_float(3.2, 3.6),
        "cell_voltage_11": get_random_float(3.2, 3.6),
        "cell_voltage_12": get_random_float(3.2, 3.6),
        "cell_voltage_13": get_random_float(3.2, 3.6),
        "cell_voltage_14": get_random_float(3.2, 3.6),
        "cell_voltage_15": get_random_float(3.2, 3.6),
        "cell_temperature_01": get_random_float(25, 40),
        "cell_temperature_02": get_random_float(25, 40),
        "cell_temperature_03": get_random_float(25, 40),
        "cell_temperature_04": get_random_float(25, 40),
        "cumulative_discharging_ah": get_random_float(100, 200),
        "cumulative_discharging_kwh": get_random_float(100, 200),
        "battery_count": 4,
    }

    payload_battery = json.dumps(battery_message)

    cmd4 = f"mosquitto_pub --cafile rootcert.pem --cert {cert_file_name} --key {key_file_name} -h {ENDPOINT} -p 8883 -q 1 -t {topic_battery} -I anyclientID --tls-version tlsv1.2 -m '{payload_battery}' -d"
    pub4 = subprocess.getoutput(cmd4)
    print(pub4)

    # environment Data
    environment_data = {
        "device_id": "FPC-device-" + DOCKER_ID,
        "temperature": get_random_float(10, 80),
        "humidity": get_random_float(10, 80),
        "fuel_level_sensor": get_random_float(10, 80),
    }

    payload_env = json.dumps(environment_data)

    cmd5 = f"mosquitto_pub --cafile rootcert.pem --cert {cert_file_name} --key {key_file_name} -h {ENDPOINT} -p 8883 -q 1 -t {topic_env} -I anyclientID --tls-version tlsv1.2 -m '{payload_env}' -d"
    pub5 = subprocess.getoutput(cmd5)
    print(pub5)

    loopcount = loopcount + 1
    time.sleep(60)
