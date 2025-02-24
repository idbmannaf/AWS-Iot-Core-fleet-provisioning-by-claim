#!/usr/bin/env python3.7

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0.

from __future__ import absolute_import
from __future__ import print_function
import argparse
import awsiot
from awscrt import auth, http, io, mqtt
from awsiot import iotidentity
from awsiot import mqtt_connection_builder
from concurrent.futures import Future
import sys
import threading
import time
import traceback
from uuid import uuid4
import json
import os

import logging

#
# configure logging
#
# logger = logging.getLogger("AWSIoTPythonSDK.core")
logger = logging.getLogger()
logger.setLevel(logging.INFO)
streamHandler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    "%(asctime)s %(levelname)s: %(filename)s:%(lineno)s - %(funcName)s: %(message)s"
)
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# - Overview -
# This sample uses the AWS IoT Fleet Provisioning to provision device using either the keys
# or CSR
#
#
# - Instructions -
# This sample requires you to create a provisioning claim. See:
# https://docs.aws.amazon.com/iot/latest/developerguide/provision-wo-cert.html
#
# - Detail -
# On startup, the script subscribes to topics based on the request type of either CSR or Keys
# publishes the request to corresponding topic and calls RegisterThing.

parser = argparse.ArgumentParser(description="Fleet Provisioning sample script.")
parser.add_argument(
    "--endpoint",
    required=True,
    help="Your AWS IoT custom endpoint, not including a port. "
    + 'Ex: "w6zbse3vjd5b4p-ats.iot.us-west-2.amazonaws.com"',
)
parser.add_argument(
    "--cert", help="File path to your client certificate, in PEM format"
)
parser.add_argument("--key", help="File path to your private key file, in PEM format")
parser.add_argument(
    "--root-ca",
    help="File path to root certificate authority, in PEM format. "
    + "Necessary if MQTT server uses a certificate that's not already in "
    + "your trust store",
)
parser.add_argument(
    "--client-id", default="test-" + str(uuid4()), help="Client ID for MQTT connection."
)
parser.add_argument(
    "--use-websocket",
    default=False,
    action="store_true",
    help="To use a websocket instead of raw mqtt. If you "
    + "specify this option you must specify a region for signing, you can also enable proxy mode.",
)
parser.add_argument(
    "--signing-region",
    default="us-east-1",
    help="If you specify --use-web-socket, this "
    + "is the region that will be used for computing the Sigv4 signature",
)
parser.add_argument(
    "--proxy-host",
    help="Hostname for proxy to connect to. Note: if you use this feature, "
    + "you will likely need to set --root-ca to the ca for your proxy.",
)
parser.add_argument(
    "--proxy-port", type=int, default=8080, help="Port for proxy to connect to."
)
parser.add_argument(
    "--verbosity",
    choices=[x.name for x in io.LogLevel],
    default=io.LogLevel.NoLogs.name,
    help="Logging level",
)
parser.add_argument("--csr", help="File path to your client CSR in PEM format")
parser.add_argument("--templateName", help="Template name")
parser.add_argument("--templateParameters", help="Values for Template Parameters")

# Using globals to simplify sample code
is_sample_done = threading.Event()
args = parser.parse_args()

io.init_logging(getattr(io.LogLevel, args.verbosity), "stderr")
mqtt_connection = None
identity_client = None

createKeysAndCertificateResponse = None
createCertificateFromCsrResponse = None
registerThingResponse = None


class LockedData(object):
    def __init__(self):
        self.lock = threading.Lock()
        self.disconnect_called = False


locked_data = LockedData()


# Function for gracefully quitting this sample
def exit(msg_or_exception):
    if isinstance(msg_or_exception, Exception):
        logger.error("Exiting Sample due to exception.")
        traceback.print_exception(
            msg_or_exception.__class__, msg_or_exception, sys.exc_info()[2]
        )
    else:
        logger.info("Exiting Sample: {}".format(msg_or_exception))

    with locked_data.lock:
        if not locked_data.disconnect_called:
            logger.info("Disconnecting...")
            locked_data.disconnect_called = True
            future = mqtt_connection.disconnect()
            future.add_done_callback(on_disconnected)


def on_disconnected(disconnect_future):
    # type: (Future) -> None
    logger.info("Disconnected.")

    # Signal that sample is finished
    is_sample_done.set()


def on_publish_register_thing(future):
    # type: (Future) -> None
    try:
        future.result()  # raises exception if publish failed
        logger.info("Published RegisterThing request..")

    except Exception as e:
        logger.error("Failed to publish RegisterThing request.")
        exit(e)


def on_publish_create_keys_and_certificate(future):
    # type: (Future) -> None
    try:
        future.result()  # raises exception if publish failed
        logger.info("Published CreateKeysAndCertificate request..")

    except Exception as e:
        logger.error("Failed to publish CreateKeysAndCertificate request.")
        exit(e)


def on_publish_create_certificate_from_csr(future):
    # type: (Future) -> None
    try:
        future.result()  # raises exception if publish failed
        logger.info("Published CreateCertificateFromCsr request..")

    except Exception as e:
        logger.error("Failed to publish CreateCertificateFromCsr request.")
        exit(e)


def createkeysandcertificate_execution_accepted(response):
    # type: (iotidentity.CreateKeysAndCertificateResponse) -> None
    try:
        global createKeysAndCertificateResponse
        createKeysAndCertificateResponse = response
        logger.info(
            "Received a new message {}".format(createKeysAndCertificateResponse)
        )
        time.sleep(2)

        return

    except Exception as e:
        exit(e)


def createkeysandcertificate_execution_rejected(rejected):
    # type: (iotidentity.RejectedError) -> None
    exit(
        "CreateKeysAndCertificate Request rejected with code:'{}' message:'{}' statuscode:'{}'".format(
            rejected.error_code, rejected.error_message, rejected.status_code
        )
    )


def createcertificatefromcsr_execution_accepted(response):
    # type: (iotidentity.CreateCertificateFromCsrResponse) -> None
    try:
        global createCertificateFromCsrResponse
        createCertificateFromCsrResponse = response
        logger.info(
            "Received a new message {}".format(createCertificateFromCsrResponse)
        )
        time.sleep(2)
        global certificateOwnershipToken
        certificateOwnershipToken = response.certificate_ownership_token

        return

    except Exception as e:
        exit(e)


def createcertificatefromcsr_execution_rejected(rejected):
    # type: (iotidentity.RejectedError) -> None
    exit(
        "CreateCertificateFromCsr Request rejected with code:'{}' message:'{}' statuscode:'{}'".format(
            rejected.error_code, rejected.error_message, rejected.status_code
        )
    )


def registerthing_execution_accepted(response):
    # type: (iotidentity.RegisterThingResponse) -> None
    try:
        global registerThingResponse
        registerThingResponse = response
        logger.info("Received a new message {} ".format(registerThingResponse))
        logger.debug(registerThingResponse.device_configuration)
        logger.debug(registerThingResponse.thing_name)
        logger.debug(createKeysAndCertificateResponse.certificate_pem)
        logger.debug(createKeysAndCertificateResponse.private_key)

        # Ensure the paths are within the persistent storage directory
        persist_path = "/opt/iotdevice/persist"

        cert_file_name = os.path.join(
            persist_path, "{}.certificate.pem".format(registerThingResponse.thing_name)
        )
        key_file_name = os.path.join(
            persist_path, "{}.private.key".format(registerThingResponse.thing_name)
        )
        # cert_file_name = '{}.certificate.pem'.format(registerThingResponse.thing_name)
        # key_file_name = '{}.private.key'.format(registerThingResponse.thing_name)
        with open(cert_file_name, "w") as f:
            f.write(createKeysAndCertificateResponse.certificate_pem)
        with open(key_file_name, "w") as f:
            f.write(createKeysAndCertificateResponse.private_key)

        logger.info(
            "wrote files: cert_file_name: {} key_file_name: {}".format(
                cert_file_name, key_file_name
            )
        )

        time.sleep(2)
        return

    except Exception as e:
        exit(e)


def registerthing_execution_rejected(rejected):
    # type: (iotidentity.RejectedError) -> None
    exit(
        "RegisterThing Request rejected with code:'{}' message:'{}' statuscode:'{}'".format(
            rejected.error_code, rejected.error_message, rejected.status_code
        )
    )


# Callback when connection is accidentally lost.
def on_connection_interrupted(connection, error, **kwargs):
    logger.error("Connection interrupted. error: {}".format(error))


# Callback when an interrupted connection is re-established.
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    logger.info(
        "Connection resumed. return_code: {} session_present: {}".format(
            return_code, session_present
        )
    )

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        logger.info("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(on_resubscribe_complete)


def on_resubscribe_complete(resubscribe_future):
    resubscribe_results = resubscribe_future.result()
    logger.info("Resubscribe results: {}".format(resubscribe_results))

    for topic, qos in resubscribe_results["topics"]:
        if qos is None:
            sys.exit("Server rejected resubscribe to topic: {}".format(topic))


def waitForCreateKeysAndCertificateResponse():
    # Wait for the response.
    loopCount = 0
    while loopCount < 10 and createKeysAndCertificateResponse is None:
        if createKeysAndCertificateResponse is not None:
            break
        logger.info(
            "Waiting... CreateKeysAndCertificateResponse: "
            + json.dumps(createKeysAndCertificateResponse)
        )
        loopCount += 1
        time.sleep(1)


def waitForCreateCertificateFromCsrResponse():
    # Wait for the response.
    loopCount = 0
    while loopCount < 10 and createCertificateFromCsrResponse is None:
        if createCertificateFromCsrResponse is not None:
            break
        logger.info(
            "Waiting...CreateCertificateFromCsrResponse: "
            + json.dumps(createCertificateFromCsrResponse)
        )
        loopCount += 1
        time.sleep(1)


def waitForRegisterThingResponse():
    # Wait for the response.
    loopCount = 0
    while loopCount < 20 and registerThingResponse is None:
        if registerThingResponse is not None:
            break
        loopCount += 1
        logger.info(
            "Waiting... RegisterThingResponse: " + json.dumps(registerThingResponse)
        )
        time.sleep(1)


if __name__ == "__main__":
    # Spin up resources
    event_loop_group = io.EventLoopGroup(1)
    host_resolver = io.DefaultHostResolver(event_loop_group)
    client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

    if args.use_websocket == True:
        proxy_options = None
        if args.proxy_host:
            proxy_options = http.HttpProxyOptions(
                host_name=args.proxy_host, port=args.proxy_port
            )

        credentials_provider = auth.AwsCredentialsProvider.new_default_chain(
            client_bootstrap
        )
        mqtt_connection = mqtt_connection_builder.websockets_with_default_aws_signing(
            endpoint=args.endpoint,
            client_bootstrap=client_bootstrap,
            region=args.signing_region,
            credentials_provider=credentials_provider,
            websocket_proxy_options=proxy_options,
            on_connection_interrupted=on_connection_interrupted,
            on_connection_resumed=on_connection_resumed,
            ca_filepath=args.root_ca,
            client_id=args.client_id,
            clean_session=False,
            keep_alive_secs=6,
        )

    else:
        mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint=args.endpoint,
            cert_filepath=args.cert,
            pri_key_filepath=args.key,
            client_bootstrap=client_bootstrap,
            ca_filepath=args.root_ca,
            client_id=args.client_id,
            on_connection_interrupted=on_connection_interrupted,
            on_connection_resumed=on_connection_resumed,
            clean_session=False,
            keep_alive_secs=6,
        )

    logger.info(
        "Connecting to {} with client ID '{}'...".format(args.endpoint, args.client_id)
    )

    connected_future = mqtt_connection.connect()

    identity_client = iotidentity.IotIdentityClient(mqtt_connection)

    # Wait for connection to be fully established.
    # Note that it's not necessary to wait, commands issued to the
    # mqtt_connection before its fully connected will simply be queued.
    # But this sample waits here so it's obvious when a connection
    # fails or succeeds.
    connected_future.result()
    logger.info("Connected!")

    # Changed By Mannaf Starting
    # Check if the Docker ID file exists and set the DOCKER_ID environment variable
    DOCKER_ID_FILE = "/opt/iotdevice/DOCKER_ID"
    if os.path.isfile(DOCKER_ID_FILE):
        with open(DOCKER_ID_FILE, "r") as f:
            DOCKER_ID = f.read().strip()
            # Set the DOCKER_ID environment variable
            os.environ["DOCKER_ID"] = DOCKER_ID
            print("Docker ID Found")
    else:
        print("DOCKER_ID file not found")

    # Construct the certificate file name
    certificate_file = "FPC-device-{}.certificate.pem".format(DOCKER_ID)

    # Changed By Mannaf Endings

    directory_path = "/opt/iotdevice/persist"

    # Find files ending with .certificate.pem and .private.key
    # certificate_files = [
    #     f for f in os.listdir(directory_path) if f.endswith(".certificate.pem")
    # ]
    # private_key_files = [
    #     f for f in os.listdir(directory_path) if f.endswith(".private.key")
    # ]

    if not os.path.isfile(os.path.join(directory_path, certificate_file)):
        try:
            # Subscribe to necessary topics.
            # Note that is **is** important to wait for "accepted/rejected" subscriptions
            # to succeed before publishing the corresponding "request".

            # Keys workflow if csr is not provided
            if args.csr is None:
                createkeysandcertificate_subscription_request = (
                    iotidentity.CreateKeysAndCertificateSubscriptionRequest()
                )

                logger.info("Subscribing to CreateKeysAndCertificate Accepted topic...")
                createkeysandcertificate_subscribed_accepted_future, _ = (
                    identity_client.subscribe_to_create_keys_and_certificate_accepted(
                        request=createkeysandcertificate_subscription_request,
                        qos=mqtt.QoS.AT_LEAST_ONCE,
                        callback=createkeysandcertificate_execution_accepted,
                    )
                )

                # Wait for subscription to succeed
                createkeysandcertificate_subscribed_accepted_future.result()

                logger.info("Subscribing to CreateKeysAndCertificate Rejected topic...")
                createkeysandcertificate_subscribed_rejected_future, _ = (
                    identity_client.subscribe_to_create_keys_and_certificate_rejected(
                        request=createkeysandcertificate_subscription_request,
                        qos=mqtt.QoS.AT_LEAST_ONCE,
                        callback=createkeysandcertificate_execution_rejected,
                    )
                )

                # Wait for subscription to succeed
                createkeysandcertificate_subscribed_rejected_future.result()
            else:
                createcertificatefromcsr_subscription_request = (
                    iotidentity.CreateCertificateFromCsrSubscriptionRequest()
                )

                logger.info("Subscribing to CreateCertificateFromCsr Accepted topic...")
                createcertificatefromcsr_subscribed_accepted_future, _ = (
                    identity_client.subscribe_to_create_certificate_from_csr_accepted(
                        request=createcertificatefromcsr_subscription_request,
                        qos=mqtt.QoS.AT_LEAST_ONCE,
                        callback=createcertificatefromcsr_execution_accepted,
                    )
                )

                # Wait for subscription to succeed
                createcertificatefromcsr_subscribed_accepted_future.result()

                logger.info("Subscribing to CreateCertificateFromCsr Rejected topic...")
                createcertificatefromcsr_subscribed_rejected_future, _ = (
                    identity_client.subscribe_to_create_certificate_from_csr_rejected(
                        request=createcertificatefromcsr_subscription_request,
                        qos=mqtt.QoS.AT_LEAST_ONCE,
                        callback=createcertificatefromcsr_execution_rejected,
                    )
                )

                # Wait for subscription to succeed
                createcertificatefromcsr_subscribed_rejected_future.result()

            registerthing_subscription_request = (
                iotidentity.RegisterThingSubscriptionRequest(
                    template_name=args.templateName
                )
            )

            logger.info("Subscribing to RegisterThing Accepted topic...")

            registerthing_subscribed_accepted_future, _ = (
                identity_client.subscribe_to_register_thing_accepted(
                    request=registerthing_subscription_request,
                    qos=mqtt.QoS.AT_LEAST_ONCE,
                    callback=registerthing_execution_accepted,
                )
            )

            # Wait for subscription to succeed
            registerthing_subscribed_accepted_future.result()

            logger.info("Subscribing to RegisterThing Rejected topic...")
            registerthing_subscribed_rejected_future, _ = (
                identity_client.subscribe_to_register_thing_rejected(
                    request=registerthing_subscription_request,
                    qos=mqtt.QoS.AT_LEAST_ONCE,
                    callback=registerthing_execution_rejected,
                )
            )
            # Wait for subscription to succeed
            registerthing_subscribed_rejected_future.result()

            if args.csr is None:
                logger.info("Publishing to CreateKeysAndCertificate...")
                publish_future = identity_client.publish_create_keys_and_certificate(
                    request=iotidentity.CreateKeysAndCertificateRequest(),
                    qos=mqtt.QoS.AT_LEAST_ONCE,
                )
                publish_future.add_done_callback(on_publish_create_keys_and_certificate)

                waitForCreateKeysAndCertificateResponse()

                if createKeysAndCertificateResponse is None:
                    raise Exception("CreateKeysAndCertificate API did not succeed")

                registerThingRequest = iotidentity.RegisterThingRequest(
                    template_name=args.templateName,
                    certificate_ownership_token=createKeysAndCertificateResponse.certificate_ownership_token,
                    parameters=json.loads(args.templateParameters),
                )
            else:
                logger.info("Publishing to CreateCertificateFromCsr...")
                csrPath = open(args.csr, "r").read()
                publish_future = identity_client.publish_create_certificate_from_csr(
                    request=iotidentity.CreateCertificateFromCsrRequest(
                        certificate_signing_request=csrPath
                    ),
                    qos=mqtt.QoS.AT_LEAST_ONCE,
                )
                publish_future.add_done_callback(on_publish_create_certificate_from_csr)

                waitForCreateCertificateFromCsrResponse()

                if createCertificateFromCsrResponse is None:
                    raise Exception("CreateCertificateFromCsr API did not succeed")

                registerThingRequest = iotidentity.RegisterThingRequest(
                    template_name=args.templateName,
                    certificate_ownership_token=createCertificateFromCsrResponse.certificate_ownership_token,
                    parameters=json.loads(args.templateParameters),
                )

            logger.info("Publishing to RegisterThing topic...")
            registerthing_publish_future = identity_client.publish_register_thing(
                registerThingRequest, mqtt.QoS.AT_LEAST_ONCE
            )
            registerthing_publish_future.add_done_callback(on_publish_register_thing)

            waitForRegisterThingResponse()
            exit("fleet provisioning finished")

        except Exception as e:
            exit(e)

        # Wait for the sample to finish
        is_sample_done.wait()
    else:
        pass
