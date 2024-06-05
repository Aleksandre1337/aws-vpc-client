import os
import logging
import botocore.exceptions
from botocore.exceptions import ClientError
import boto3
import argparse
from dotenv import load_dotenv
from os import getenv
import ipaddress

dotenv_path = '.env'
load_dotenv(dotenv_path)

ec2_client = boto3.client(
  "ec2",
  aws_access_key_id=getenv("aws_access_key_id"),
  aws_secret_access_key=getenv("aws_secret_access_key"),
  aws_session_token=getenv("aws_session_token"),
  region_name=getenv("aws_region_name")
)

ec2_resource = boto3.resource(
  'ec2',
  aws_access_key_id=getenv("aws_access_key_id"),
  aws_secret_access_key=getenv("aws_secret_access_key"),
  aws_session_token=getenv("aws_session_token"),
  region_name=getenv("aws_region_name"))


def list_vpcs(vpc_id):
  if vpc_id:
    response = ec2_client.describe_vpcs(VpcIds=[vpc_id])
    print(response)
  else:
    response = ec2_client.describe_vpcs()

  for vpc in response["Vpcs"]:
    vpc_id = vpc["VpcId"]
    vpc_state = vpc["State"]
    vpc_name = "No Tags"
    vpc_instance_tenancy = vpc['InstanceTenancy']
    vpc_cidr_block = vpc['CidrBlock']
    vpc_cidr_block_association_set = vpc['CidrBlockAssociationSet']
    for item in vpc_cidr_block_association_set:
      if "AssociationId" in item:
        vpc_associationid = item['AssociationId']
        vpc_cidr_block = item['CidrBlock']
        vpc_cidr_block_state = item['CidrBlockState']['State']
    if "Tags" in vpc:
      for tag in vpc["Tags"]:
        vpc_name = tag["Value"]
        break
    print("")
    print("-----------------------------")
    print(f"VPC ID: {vpc_id}")
    print(f"VPC Name: {vpc_name}")
    print(f"VPC State: {vpc_state}")
    print(f'VPC Instance Tenancy: {vpc_instance_tenancy}')
    print(f'VPC CIDR Block: {vpc_cidr_block}')
    print(f'VPC CIDR Block Association ID: {vpc_associationid}')
    print(f'VPC CIDR Block State: {vpc_cidr_block_state}')
    print("-----------------------------")

def validate_cidr_block(value):
  try:
    ipaddress.IPv4Network(value)
    return value
  except ValueError:
    raise argparse.ArgumentTypeError(f"{value} is not a valid CIDR block")

def create_vpc(CidrBlock):
    try:
        response = ec2_client.create_vpc(CidrBlock=str(CidrBlock))
        response.wait_until_available()
        vpc = response.get("Vpc")

        vpc_id = vpc.get('VpcId')
        vpc_state = vpc.get('State')
        vpc_instance_tenancy = vpc.get('InstanceTenancy')
        vpc_cidr_block = vpc.get('CidrBlock')
        vpc_associationid = vpc.get('CidrBlockAssociationSet')[0].get('AssociationId')
        vpc_cidr_block_state = vpc.get('CidrBlockAssociationSet')[0].get('CidrBlockState').get('State')

        print("\n-----------------------------")
        print(f"VPC ID: {vpc_id}")
        print(f"VPC State: {vpc_state}")
        print(f'VPC Instance Tenancy: {vpc_instance_tenancy}')
        print(f'VPC CIDR Block: {vpc_cidr_block}')
        print(f'VPC CIDR Block Association ID: {vpc_associationid}')
        print(f'VPC CIDR Block State: {vpc_cidr_block_state}')
        print("-----------------------------")

    except ClientError as e:
        logging.error(e)


def create_subnets(vpc_id, public_cidr_block, private_cidr_block):
  try:
      # Validate the CIDR blocks
      public_cidr_block = validate_cidr_block(public_cidr_block)
      private_cidr_block = validate_cidr_block(private_cidr_block)

      # Create the route table
      rt_public = ec2_client.create_route_table(VpcId=vpc_id)
      print(f'Public Route Table Created with ID: {rt_public["RouteTable"]["RouteTableId"]}')

      # Create the public subnet
      subnet_public = ec2_client.create_subnet(CidrBlock=public_cidr_block, VpcId=vpc_id)
      print(f"Public Subnet Created with ID: {subnet_public['Subnet']['SubnetId']}")

      # Create the private subnet
      subnet_private = ec2_client.create_subnet(CidrBlock=private_cidr_block, VpcId=vpc_id)
      print(f"Private Subnet Created with ID: {subnet_private['Subnet']['SubnetId']}")

      return vpc_id, subnet_public['Subnet']['SubnetId'], subnet_private['Subnet']['SubnetId']
  except ClientError as e:
      print(f"An error occurred: {e}")


def add_name_tag(resource_id, resource_name):
  try:
    response = ec2_client.create_tags(Resources=[resource_id],
                          Tags=[{
                            "Key": "Name",
                            "Value": str(resource_name)
                          }])
    if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
      print(f"Name tag: {resource_name} added to Resource: {resource_id}")
  except ClientError as e:
    logging.error(e)

def create_igw():
  try:
    response = ec2_client.create_internet_gateway()
    igw_id = response["InternetGateway"]["InternetGatewayId"]
    print("")
    print("Status: Created")
    print('f"Internet Gateway ID: {igw_id}"')
  except ClientError as e:
    logging.error(e)

def attach_igw_to_vpc(vpc_id, igw_id):
  try:
    response = ec2_client.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
    print(f"Internet Gateway: {igw_id} attached to VPC: {vpc_id}")
  except ClientError as e:
    logging.error(e)

def detach_igw_from_vpc(vpc_id, igw_id):
  try:
    response = ec2_client.detach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
    print(f"Internet Gateway: {igw_id} detached from VPC: {vpc_id}")
  except ClientError as e:
    logging.error(e)


def create_ec2_full(vpc_id):
  try:
    # Create a security group with HTTP and SSH ingress rules
    try:
      response = ec2_client.create_security_group(GroupName="webserver", Description="Allow HTTP and SSH access", VpcId=vpc_id)
      security_group_id = response['GroupId']
      ec2_client.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            {'IpProtocol': 'tcp',
             'FromPort': 22,
             'ToPort': 22,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol': 'tcp',
             'FromPort': 80,
             'ToPort': 80,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        ])
      print(f"Security Group {security_group_id} created successfully.")
    except botocore.exceptions.ClientError as e:
      if e.response['Error']['Code'] == 'InvalidGroup.Duplicate':
        print("Security group already exists, continuing...")
      # Retrieve the security group ID of the existing security group
        response = ec2_client.describe_security_groups(GroupNames=['webserver'])
        security_group_id = response['SecurityGroups'][0]['GroupId']
      else:
        raise
    # Create KeyPair for EC2 Instance
    try:
      ec2_client.create_key_pair(KeyName='ec2key',KeyType='rsa')
      print("KeyPair {KeyName} created successfully.")
    except botocore.exceptions.ClientError as e:
      if e.response['Error']['Code'] == 'InvalidKeyPair.Duplicate':
        print("Key pair already exists, continuing...")
      else:
        raise
    # Check if VPC has public subnets
    subnet_response = ec2_client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    subnets = subnet_response.get('Subnets', [])
    subnet_id = None
    for subnet in subnets:
      if subnet.get('MapPublicIpOnLaunch'):
        subnet_id = subnet.get('SubnetId')
        break
    if subnet_id is None:
      print("No public subnet found in the VPC")
      return
    # Create EC2 Instance
    ec2_creation = ec2_resource.create_instances(
        ImageId="ami-0e001c9271cf7f3b9",
        MinCount=1,
        MaxCount=1,
        InstanceType="t2.micro",
        KeyName="ec2key",
        SubnetId=subnet_id,
        SecurityGroupIds=[security_group_id],
        BlockDeviceMappings=[
            {
                'DeviceName': '/dev/sda1',
                'Ebs': {
                    'VolumeSize': 10,
                    'VolumeType': 'gp2'
                }
            }
        ],
        TagSpecifications=[
    {
        'ResourceType': 'instance',
        'Tags': [
            {
                'Key': 'Name',
                'Value': 'MyEC2Instance'
            },
        ]
    },
]
    )
    if ec2_creation:
      instance=ec2_creation[0]
      print(f"EC2 Instance {instance.id} created successfully.")
      print("Please wait for the instance to be in running state for more information...")
      instance.wait_until_running()
      instance.load()
      instance_description = ec2_client.describe_instances(InstanceIds=[instance.id])
      instance_info = instance_description['Reservations'][0]['Instances'][0]
      print("")
      print(f"Instance ID: {instance_info['InstanceId']}")
      print(f"Instance Type: {instance_info['InstanceType']}")
      print(f"AMI ID: {instance_info['ImageId']}")
      print(f"Launch Time: {instance_info['LaunchTime']}")
      print(f"VPC ID: {instance_info['VpcId']}")
      print(f"State: {instance_info['State']['Name']}")
      print(f"Public IP: {instance_info.get('PublicIpAddress', 'N/A')}")
      print(f"Private IP: {instance_info['PrivateIpAddress']}")
      print(f"Availability Zone: {instance_info['Placement']['AvailabilityZone']}")
    else:
      print("Failed to create EC2 instance.")
  except ClientError as e:
    print(f"An error occurred: {e}")

def argument_list():
  parser = argparse.ArgumentParser(description="List VPCs")
  parser.add_argument("--list", nargs='?', const=None, default=False, help="List VPCs. Provide VPC ID to list a specific VPC.")
  parser.add_argument("--create", nargs=1, help="Create VPC by entering a CIDR Block", type=validate_cidr_block)
  parser.add_argument("--tag", nargs=2, help="Add a Name tag to a VPC, IGW and other resources", type=str)
  parser.add_argument("--create-subnets", nargs=3, help="Create Subnets in a VPC, arguments: vpc_id, public_cidr_block, private_cidr_block", type=str)
  parser.add_argument("--create-igw", help="Create an Internet Gateway", action="store_true")
  parser.add_argument("--attach-igw", nargs=2, help="Attach an Internet Gateway to a VPC")
  parser.add_argument("--detach-igw", nargs=2, help="Detach an Internet Gateway from a VPC", type=str)
  parser.add_argument("--create-ec2", nargs=1, help="Creates an EC2 Instance with Security Group [SSH, HTTP], and KeyPair. Enter VPC ID to begin")

  return parser.parse_args()

def main():
  if args.list != False:
      list_vpcs(args.list)
  elif args.create:
      create_vpc(args.create[0])
  elif args.tag:
      add_name_tag(args.tag[0], args.tag[1])
  elif args.create_igw:
      create_igw()
  elif args.attach_igw:
      attach_igw_to_vpc(args.attach_igw[0], args.attach_igw[1])
  elif args.detach_igw:
      detach_igw_from_vpc(args.detach_igw[0], args.detach_igw[1])
  elif args.create_subnets:
      create_subnets(args.create_subnets[0], args.create_subnets[1], args.create_subnets[2])
  elif args.create_ec2:
      create_ec2_full(args.create_ec2[0])

if __name__ == "__main__":
    args = argument_list()
    main()
