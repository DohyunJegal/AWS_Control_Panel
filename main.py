from datetime import datetime, timedelta
from botocore.exceptions import ClientError

import boto3
import botocore
import paramiko as paramiko

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
cloudwatch = boto3.client('cloudwatch', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=region)

# EC2 인스턴스 목록 가져오기
ec2 = session.client('ec2')


def listInstance():
    try:
        instances = ec2.describe_instances()

        for instance in instances['Reservations']:
            for instance_detail in instance['Instances']:
                print(f'[Name] {instance_detail["Tags"][0]["Value"]:>15} [id] {instance_detail["InstanceId"]} [AMI] {instance_detail["ImageId"]} [type] {instance_detail["InstanceType"]} [state] {instance_detail["State"]["Name"]:>10} [monitoring state] {instance_detail["Monitoring"]["State"]}')

        if 'NextToken' in instances:
            next_token = instances['NextToken']

            while next_token:
                instances = ec2.describe_instances(NextToken=next_token)

                for instance in instances['Reservations']:
                    for instance_detail in instance['Instances']:
                        print(f'[Name] {instance_detail["Tags"][0]["Value"]:>15} [id] {instance_detail["InstanceId"]} [AMI] {instance_detail["ImageId"]} [type] {instance_detail["InstanceType"]} [state] {instance_detail["State"]["Name"]:>10} [monitoring state] {instance_detail["Monitoring"]["State"]}')

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

    print('Enter new instance name: ', end='')
    new_instance_name = input().rstrip()

    try:
        new_instance = ec2.run_instances(
            ImageId=ami_id,
            InstanceType='t2.micro',
            MinCount=1,
            MaxCount=1,
            TagSpecifications=[{
                'ResourceType': 'instance',
                'Tags': [{
                    'Key': 'Name',
                    'Value': new_instance_name
                }]
            }]
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


def instanceStatus():
    try:
        instance = ec2.describe_instances(InstanceIds=['i-0aec95ffbdd45add5'])
    except ClientError as e:
        print(f'There is no main instance\n--> {e}')
        return

    try:
        public_ip = instance['Reservations'][0]['Instances'][0]['PublicIpAddress']
    except KeyError as e:
        print(f'No main instance running\n--> cannot get {e}')
        return

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=public_ip, username='ec2-user', key_filename='./.aws/cloud-ec2.pem')

        # Run the condor_status command
        stdin, stdout, stderr = client.exec_command('condor_status')

        # Print the output of the condor_status command
        print(stdout.read().decode())

        client.close()
    except ClientError as e:
        print(f'Failed to check status instance: {e}')


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


def checkUtilization(instance_id, start_time, end_time):
    try:
        ec2.describe_instances(InstanceIds=[instance_id])
    except ClientError as e:
        print(f'No instance \'{instance_id}\'\n--> {e}')
        return

    def checkCloudwatch(metric):
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName=metric,
            Dimensions=[{
                'Name': 'InstanceId',
                'Value': instance_id
            }],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,     # 1시간
            Statistics=['Average']
        )['Datapoints']

        total_usage = sum(data['Average'] for data in response)
        average_usage = total_usage/len(response)
        max_usage = max(data['Average'] for data in response)
        min_usage = min(data['Average'] for data in response)

        print(f'[{metric}] average: {round(float(average_usage), 3)}, max: {round(float(max_usage), 3)}, min: {round(float(min_usage), 3)}')

    print()
    checkCloudwatch('CPUUtilization')
    checkCloudwatch('DiskReadBytes')
    checkCloudwatch('DiskReadOps')
    checkCloudwatch('DiskWriteBytes')
    checkCloudwatch('DiskWriteOps')
    checkCloudwatch('NetworkIn')
    checkCloudwatch('NetworkPacketsIn')
    checkCloudwatch('NetworkOut')
    checkCloudwatch('NetworkPacketsOut')


if __name__ == "__main__":
    while True:
        print("                                                            ")
        print("------------------------------------------------------------")
        print("                  AWS Control Panel                         ")
        print("------------------------------------------------------------")
        print("  1. available regions            2. available zones        ")
        print("  3. list images                  4. list instance          ")
        print("  5. create instance              6. start instance         ")
        print("  7. stop instance                8. reboot instance        ")
        print("  9. terminate instance          10. check instance status  ")
        print(" 11. start all instances         12. stop all instances     ")
        print(" 13. reboot all instances        14. create multiple instances")
        print(" 15. check instance utilization                             ")
        print("                                 99. quit                   ")
        print("------------------------------------------------------------")
        print("Enter an integer: ", end='')

        menu = input().rstrip()
        instance_id = ''

        print('')

        if menu == '1':
            availableRegions()
        elif menu == '2':
            availableZones()
        elif menu == '3':
            listImages()
        elif menu == '4':
            listInstance()
        elif menu == '5':
            print('Enter AMI id: ', end='')
            ami_id = input().rstrip()

            if ami_id != '':
                createInstance(ami_id)
        elif menu == '6':
            print('Enter instance id: ', end='')
            instance_id = input().rstrip()

            if instance_id != '':
                startInstance(instance_id)
        elif menu == '7':
            print('Enter instance id: ', end='')
            instance_id = input().rstrip()

            if instance_id != '':
                stopInstance(instance_id)
        elif menu == '8':
            print('Enter instance id: ', end='')
            instance_id = input().rstrip()

            if instance_id != '':
                rebootInstance(instance_id)
        elif menu == '9':
            print('Enter instance id: ', end='')
            instance_id = input().rstrip()

            if instance_id != '':
                terminateInstance(instance_id)
        elif menu == '10':
            instanceStatus()
        elif menu == '11':
            startAllInstances()
        elif menu == '12':
            stopAllInstances()
        elif menu == '13':
            rebootAllInstances()
        elif menu == '14':
            print('Enter AMI id: ', end='')
            ami_id = input().rstrip()
            print('Enter the number of instances : ', end='')
            n = input().rstrip()

            if ami_id != '' and n != '':
                createMultipleInstances(ami_id, n)
        elif menu == '15':
            print('Enter instance id: ', end='')
            instance_id = input().rstrip()

            print('Enter an integer to check the record from a few days ago.(value>0): ', end='')
            d = input().rstrip()

            if instance_id != '' and d != '' or '0':
                checkUtilization(instance_id, datetime.now()-timedelta(days=int(d)), datetime.now())
        elif menu == '99':
            print('bye!')
            exit(0)
        else:
            print('retry!')
