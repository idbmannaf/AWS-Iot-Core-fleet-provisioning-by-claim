#!/bin/bash
# Check if DOCKER_ID exists, if not, generate and save it
if [ ! -f "/opt/iotdevice/DOCKER_ID" ]; then
    DOCKER_ID=$(uuidgen)
    echo $DOCKER_ID > /opt/iotdevice/DOCKER_ID
else
    DOCKER_ID=$(cat /opt/iotdevice/DOCKER_ID)
fi
export DOCKER_ID
# --root-ca rootcert.pem \
# Command to run on container start
python3 fleetprovisioning.py --endpoint $ENDPOINT \
    --root-ca /opt/iotdevice/rootcert.pem \
    --cert provision-claim.certificate.pem \
    --key provision-claim.private.key \
    --client-id fleet-device \
    --templateName TestFleetProvisioningTemplate \
    --templateParameters "{\"DeviceName\":\"FPC-device-${DOCKER_ID}\",\"SerialNumber\":\"123456\",\"DeviceLocation\":\"Berlin\"}" && \
    python3 simple_simulator.py
