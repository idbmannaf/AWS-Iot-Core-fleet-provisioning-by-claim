# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import os
import subprocess
import json
import argparse
import time


# Pass argument into variables
parser = argparse.ArgumentParser()
parser.add_argument(
    "-e",
    "--endpoint",
    action="store",
    required=True,
    dest="endpoint",
    help="regional AWS IoT Core AT endpoint",
)
parser.add_argument(
    "-n",
    "--fleetsize",
    action="store",
    required=True,
    dest="fleetsize",
    help="Numbers of device on the simulated fleet",
)

args = parser.parse_args()
endpoint = args.endpoint
number_of_devices = int(args.fleetsize)


print(f"The endpoint is {endpoint}")
print(f"Deploying fleet of {number_of_devices} devices")


def generate_unique_container_id():
    current_time = time.time()
    current_time_int = int(current_time)
    return current_time_int


for n in range(1, number_of_devices + 1):
    container_id = generate_unique_container_id()
    subprocess.getoutput(f"docker volume create device{container_id}_volume")
    create_container = subprocess.getoutput(
        f"docker run -d --network host -e ENDPOINT={endpoint} --name device{container_id} -v device{container_id}_volume:/opt/iotdevice/persist my_new_imagefile >> docker.logs"
    )
    print(f"Creating device{container_id} with device{container_id}_volume")

    time.sleep(10)
