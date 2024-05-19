# vpc_boto3

This Python script uses the boto3 library to interact with Amazon Web Services (AWS) to manage Virtual Private Clouds (VPCs). It provides functionality to list, create, and tag VPCs, as well as create and attach Internet Gateways.

## Requirements

- Python 3
- boto3 library
- dotenv library
- AWS account with access to EC2 service

## Setup

1. Install the required Python libraries with pip:

```bash
pip install setup.py
```

2. Create a `.env` file in the same directory as the script, and add your AWS credentials and region:

```env


aws

_access_key_id=YOUR_ACCESS_KEY
aws_secret_access_key=YOUR_SECRET_KEY
aws_session_token=YOUR_SESSION_TOKEN
aws_region_name=YOUR_REGION_NAME
```

## Usage

The script provides several command-line arguments for different operations:

- `--list [VPC_ID]`: List all VPCs or a specific VPC if VPC_ID is provided.
- `--create CIDR_BLOCK`: Create a new VPC with the specified CIDR block.
- `--tag RESOURCE_ID RESOURCE_NAME`: Add a name tag to a resource.
- `--create-igw`: Create a new Internet Gateway.
- `--attach-igw VPC_ID IGW_ID`: Attach an Internet Gateway to a VPC.

Example usage:

```bash
python vpc_boto3.py --list
python vpc_boto3.py --create 10.0.0.0/16
python vpc_boto3.py --tag vpc-abcdefgh MyVPC
python vpc_boto3.py --create-igw
python vpc_boto3.py --attach-igw vpc-abcdefgh igw-abcdefgh
```

## Note

This script does not handle error checking beyond basic AWS API error responses. Use with caution in a production environment.