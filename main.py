import boto3
import botocore
from botocore.exceptions import ClientError

# '.aws/config'에서 region 값 호출
with open("./.aws/config") as config_file:
    config = config_file.read()
    region = config.split("region = ")[1].split("\n")[0]

# '.aws/credentials'에서 키 값 호출
with open("./.aws/credentials") as credentials_file:
    credentials = credentials_file.read()
    aws_access_key_id = credentials.split('aws_access_key_id = ')[1].split("\n")[0]
    aws_secret_access_key = credentials.split('aws_secret_access_key = ')[1].split("\n")[0]

# boto3 세션 객체 생성
session = boto3.Session(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=region)

# EC2 인스턴스 목록 가져오기
ec2 = session.client('ec2')


def listInstance():
    try:
        instances = ec2.describe_instances()

        for instance in instances['Reservations']:
            for instance_detail in instance['Instances']:
                print(f'[id] {instance_detail["InstanceId"]} [AMI] {instance_detail["ImageId"]} [type] {instance_detail["InstanceType"]} [state] {instance_detail["State"]["Name"]:>10} [monitoring state] {instance_detail["Monitoring"]["State"]}')

        if 'NextToken' in instances:
            next_token = instances['NextToken']

            while next_token:
                instances = ec2.describe_instances(NextToken=next_token)

                for instance in instances['Reservations']:
                    for instance_detail in instance['Instances']:
                        print(f'[id] {instance_detail["InstanceId"]} [AMI] {instance_detail["ImageId"]} [type] {instance_detail["InstanceType"]} [state] {instance_detail["State"]["Name"]:>10} [monitoring state] {instance_detail["Monitoring"]["State"]}')

                next_token = instances.get('NextToken')
    except ClientError as e:
        print(f'No instances\n--> {e}')
        return


def availableZones():
    zones = ec2.describe_availability_zones()

    try:
        for zone in zones['AvailabilityZones']:
            print(f'[id] {zone["ZoneId"]} [region] {zone["RegionName"]:>15} [zone] {zone["ZoneName"]:>15}')
        print('You have access to ' + str(len(zones['AvailabilityZones'])) + ' Availability Zones.')
    except ClientError as e:
        print('Caught Exception: ' + str(e))
        print('Reponse Status Code: ' + str(e.response['StatusLine']))
        print('Error Code: ' + str(e.response['Error']['Code']))
        print('Request ID: ' + str(e.response['ResponseMetadata']['RequestId']))


def startInstance(instance_id):
    try:
        ec2.describe_instances(InstanceIds=[instance_id])
    except ClientError as e:
        print(f'No instance \'{instance_id}\'\n--> {e}')
        return

    print(f'Starting {instance_id}....')

    try:
        ec2.start_instances(InstanceIds=[instance_id])
        print(f'Successfully started instance {instance_id}')
    except ClientError as e:
        print(f'Failed to start instance {instance_id}: {e}')


def availableRegions():
    regions = ec2.describe_regions()

    for region in regions['Regions']:
        print(f'[region] {region["RegionName"]:>15} [endpoint] {region["Endpoint"]}')


def stopInstance(instance_id):
    try:
        ec2.describe_instances(InstanceIds=[instance_id])
    except ClientError as e:
        print(f'No instance \'{instance_id}\'\n--> {e}')
        return

    print(f'Stopping {instance_id}....')

    try:
        ec2.stop_instances(InstanceIds=[instance_id])
        print(f'Successfully stopped instance {instance_id}')
    except ClientError as e:
        print(f'Failed to stop instance {instance_id}: {e}')


def createInstance(ami_id):
    try:
        ec2.describe_images(ImageIds=[ami_id])
    except ClientError as e:
        print(f'No AMI \'{ami_id}\'\n--> {e}')
        return

    try:
        new_instance = ec2.run_instances(
            ImageId=ami_id,
            InstanceType='t2.micro',
            MinCount=1,
            MaxCount=1
        )
        new_instance_id = new_instance['Instances'][0]['InstanceId']
        print(f'Successfully created EC2 instance {new_instance_id} based on AMI {ami_id}')
    except ClientError as e:
        print(f'Failed to create instance: {e}')


def rebootInstance(instance_id):
    try:
        ec2.describe_instances(InstanceIds=[instance_id])
    except ClientError as e:
        print(f'No instance \'{instance_id}\'\n--> {e}')
        return

    try:
        ec2.reboot_instances(InstanceIds=[instance_id])
        print(f'Successfully rebooted instance {instance_id}')
    except ClientError as e:
        print(f'Failed to reboot instance {instance_id}: {e}')


def listImages():
    images = ec2.describe_images(
        Filters=[{
            'Name': 'name',
            'Values': ['aws-htcondor-worker']
        }]
    )

    for image in images['Images']:
        print(f'[ImageID] {image["ImageId"]} [Name] {image["Name"]} [Owner] {image["OwnerId"]}')


def terminateInstance(instance_id):
    try:
        ec2.describe_instances(InstanceIds=[instance_id])
    except ClientError as e:
        print(f'No instance \'{instance_id}\'\n--> {e}')
        return

    try:
        ec2.terminate_instances(InstanceIds=[instance_id])
        print(f'Successfully terminate instance {instance_id}')
    except ClientError as e:
        print(f'Failed to terminate instance {instance_id}: {e}')


def startAllInstances():
    try:
        instances = ec2.describe_instances()

        for instance in instances['Reservations']:
            for instance_detail in instance['Instances']:
                startInstance(instance_detail["InstanceId"])
    except ClientError as e:
        print(f'No instances\n--> {e}')
        return


def stopAllInstances():
    try:
        instances = ec2.describe_instances()

        for instance in instances['Reservations']:
            for instance_detail in instance['Instances']:
                stopInstance(instance_detail["InstanceId"])
    except ClientError as e:
        print(f'No instances\n--> {e}')
        return


def rebootAllInstances():
    try:
        instances = ec2.describe_instances()

        for instance in instances['Reservations']:
            for instance_detail in instance['Instances']:
                rebootInstance(instance_detail["InstanceId"])
    except ClientError as e:
        print(f'No instances\n--> {e}')
        return


def createMultipleInstances(ami_id, n):
    if n.isnumeric():
        for i in range(int(n)):
            createInstance(ami_id)
    else:
        print('retry!')


if __name__ == "__main__":
    while True:
        print("                                                            ")
        print("------------------------------------------------------------")
        print("                  AWS Control Panel                         ")
        print("------------------------------------------------------------")
        print("  1. list instance                2. available zones        ")
        print("  3. start instance               4. available regions      ")
        print("  5. stop instance                6. create instance        ")
        print("  7. reboot instance              8. list images            ")
        print("  9. terminate instance          10. start all instances    ")
        print(" 11. stop all instances          12. reboot all instances   ")
        print(" 13. create multiple instances   99. quit                   ")
        print("------------------------------------------------------------")
        print("Enter an integer: ", end='')

        menu = input().rstrip()
        instance_id = ''

        print('')

        if menu == '1':
            listInstance()
        elif menu == '2':
            availableZones()
        elif menu == '3':
            print('Enter instance id: ', end='')
            instance_id = input().rstrip()

            if instance_id != '':
                startInstance(instance_id)
        elif menu == '4':
            availableRegions()
        elif menu == '5':
            print('Enter instance id: ', end='')
            instance_id = input().rstrip()

            if instance_id != '':
                stopInstance(instance_id)
        elif menu == '6':
            print('Enter AMI id: ', end='')
            ami_id = input().rstrip()

            if ami_id != '':
                createInstance(ami_id)
        elif menu == '7':
            print('Enter instance id: ', end='')
            instance_id = input().rstrip()

            if instance_id != '':
                rebootInstance(instance_id)
        elif menu == '8':
            listImages()
        elif menu == '9':
            print('Enter instance id: ', end='')
            instance_id = input().rstrip()

            if instance_id != '':
                terminateInstance(instance_id)
        elif menu == '10':
            startAllInstances()
        elif menu == '11':
            stopAllInstances()
        elif menu == '12':
            rebootAllInstances()
        elif menu == '13':
            print('Enter AMI id: ', end='')
            ami_id = input().rstrip()
            print('Enter the number of instances : ', end='')
            n = input().rstrip()

            if ami_id != '' and n != '':
                createMultipleInstances(ami_id, n)
        elif menu == '99':
            print('bye!')
            exit(0)
        else:
            print('retry!')
