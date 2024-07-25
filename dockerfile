FROM ubuntu:latest

WORKDIR /opt/iotdevice

# Add the application code
ADD iotdevice /opt/iotdevice

# Update and upgrade the system packages, and install necessary packages
RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install python3 -y && \
    apt-get install python3-pip -y && \
    apt-get install python3-venv -y && \
    apt-get install wget -y && \
    apt-get install uuid-runtime -y && \
    apt-get install cmake -y  # Install CMake

# Create and activate a virtual environment, and install the required packages
RUN python3 -m venv /opt/iotdevice/venv && \
    /opt/iotdevice/venv/bin/pip install --upgrade pip && \
    /opt/iotdevice/venv/bin/pip install -r /opt/iotdevice/requirements.txt

# Download the Amazon Root CA certificate
RUN wget -O /opt/iotdevice/rootcert.pem https://www.amazontrust.com/repository/AmazonRootCA1.pem

# Install mosquitto and mosquitto-clients
RUN apt-get install mosquitto -y && \
    apt-get install mosquitto-clients -y

# Use the virtual environment for any future RUN commands
ENV PATH="/opt/iotdevice/venv/bin:$PATH"

# Create a directory for persistent storage
RUN mkdir -p /opt/iotdevice/persist

# Copy the entrypoint script and make it executable
COPY entrypoint.sh /opt/iotdevice/entrypoint.sh
RUN chmod +x /opt/iotdevice/entrypoint.sh

# Set the entrypoint command
CMD ["/opt/iotdevice/entrypoint.sh"]

# # --root-ca rootcert.pem \
# # Command to run on container start
# CMD export DOCKER_ID=$(uuidgen) && \
#     python3 fleetprovisioning.py --endpoint $ENDPOINT \
#     --root-ca /opt/iotdevice/rootcert.pem \
#     --cert provision-claim.certificate.pem \
#     --key provision-claim.private.key \
#     --client-id fleet-device \
#     --templateName TestFleetProvisioningTemplate \
#     --templateParameters "{\"DeviceName\":\"FPC-device-${DOCKER_ID}\",\"SerialNumber\":\"123456\",\"DeviceLocation\":\"Berlin\"}" && \
#     python3 simple_simulator.py
