Follow the official repository [Fleet Provisioning By Claim](https://github.com/aws-samples/aws-iot-core-device-provisioning-deep-dive/tree/dev/fleet_provisioning_by_claim)

### Pre-requisites

- AWS account
- AWS cloud9 instance with the relevant permission to execute AWS IoT actions
- IAM role creation access

### Creating the Fleet Provisioning IAM role

- Go to Identity and Access Management (IAM)

  - Roles -> Create a new role
  - Select use cases, and under the drop down menu search for AWS IoT and select _IoT_
  - Next
  - Keep policies as default, next
  - Give it a name and keep the rest as default
  - Create
  - Navigate back, copy and save the role ARN.

### Building a simulation environment

- Go to AWS Cloud9

  1 - Go to AWS cloud9 -> Create environment -> give it a name

        Use the following configurations -

        - Create a new EC2 instance for environment (direct access)
        - t3.small (2 GiB RAM + 2 vCPU)
        - AmazonLinux 2

        Next step and create

- Clone the repository for the simulation and change into the directory

  ```
  git clone PLACEHOLDER
  cd fleet_provisioning_by_claim
  ```

- Create a provisioning template with AWS IoT core

  ```
  aws iot create-provisioning-template \
   --template-name FleetProvisioningTemplate \
   --provisioning-role-arn <THE PROVISIONING ROLE ARN HERE> \
   --template-body file://./fleet-provisioning-template.json \
   --enabled
  ```

- Create a claim certificate:

  ```
  THING_NAME=provision-claim
  aws iot create-keys-and-certificate --set-as-active \
  --public-key-outfile $THING_NAME.public.key \
  --private-key-outfile $THING_NAME.private.key \
  --certificate-pem-outfile $THING_NAME.certificate.pem > provisioning-claim-result.json
  ```

  Now we save the ID to a variable for the next step.

  ```
  CERTIFICATE_ARN=$(jq -r ".certificateArn" provisioning-claim-result.json)
  ```

  **Note that Claim certificate are just AWS generate x.509 certificate, what makes it into a secure claim certificate is the action of restricting it with the correct policy which we will do in the next step.**

- Attach Claim policy to claim certificate

  **Before executing the next command be sure to edit the fleet-provisioning-policy.json document with your region and AWS account ID.**

  ```
  aws iot create-policy --policy-name fleet-provisioning_Policy \
  --policy-document file://./fleet-provisioning-policy.json
  ```

  Then attach the policy to the claim cert

  ```
  aws iot attach-policy --policy-name fleet-provisioning_Policy \
  --target $CERTIFICATE_ARN
  ```

### Testing the Fleet provisioning template and deploying a fleet

For this next step we will be creating a Simulation fleet using Docker containers to simulate a IoT thing.

- Run the following commands to create a Docker image.

  ```
  mv provision-claim.certificate.pem ./iotdevice/provision-claim.certificate.pem
  mv provision-claim.private.key ./iotdevice/provision-claim.private.key
  docker build --tag golden-image-fpc .
  ```

- Now we get the endpoint for your AWS IoT core and run the simulation

      ```
      aws iot describe-endpoint \
      --endpoint-type iot:Data-ATS
      ```
      Use it to run the next command. Also feel free to simulate as many devices as you like by change the number 20 to anything else. (Keep in mind too many containers will crash your Instance if not properly sized)

      ```
      python3 simulate_fleet.py -e <YOUR-ENDPOINT-HERE> -n 20
      ```

  Check your AWS IoT Core - Under things, you should see the device populating the registry list with random UUIDs

# After complete all the step follow belows instructions (My Repository)

1. edit **fleet-provisioning-policy.json** and replace <aws-region>:<aws-account-id> to actual aws-region and aws-account-id

2. copy all files, paste and replace in the **fleet_provisioning_by_claim** at **cloud9**

```bash
# Build Docker image

docker build -t my_new_imagefile .

# Run this command for create certificates and device id and publish data to iot core
python3 simulate_fleet.py -e AWS_IOT_CORE_ENDPOINT -n NUMBER_OF_DEVICE

# Stop All containers
docker stop $(docker ps -aq)

# Remove All containers
docker rm $(docker ps -aq)

```

# Note: if you want to run this in your local machine then just download all code and run it

```bash
# Build Docker image

docker build -t my_new_imagefile .

# Run this command for create certificates and device id and publish data to iot core
python3 simulate_fleet.py -e AWS_IOT_CORE_ENDPOINT -n NUMBER_OF_DEVICE

# Stop All containers
docker stop $(docker ps -aq)

# Remove All containers
docker rm $(docker ps -aq)

```
