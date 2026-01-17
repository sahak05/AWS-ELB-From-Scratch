import time
import boto3
import textwrap

# Let's start with configuration

REGION = 'ca-central-1'
SECURITY_GROUP_NAME = 'sec-group-asg1'
KEY='first-key-pair-for-first-vps'

ec2 = boto3.resource('ec2', region_name=REGION)
ec2_client = boto3.client('ec2', region_name=REGION)


# AUTOMATED SCRIPT
ec2_user_data = USER_DATA_SCRIPT = textwrap.dedent("""#!/bin/bash
# Enable logging so we can see what went wrong in /var/log/user-data.log
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "Starting setup..."
yum update -y
yum install python3 python3-pip -y
pip3 install fastapi uvicorn requests

echo "Creating Python App..."
# Note: The EOF block must be fully left-aligned in the final file
cat <<'EOF' > /home/ec2-user/main.py
from fastapi import FastAPI
import socket

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Instance is responding!", "instance_id": socket.gethostname()}

@app.get("/cluster1")
def read_cluster1():
    return {"message": "Cluster 1 (Small) responding", "instance_id": socket.gethostname()}

@app.get("/cluster2")
def read_cluster2():
    return {"message": "Cluster 2 (Micro) responding", "instance_id": socket.gethostname()}
EOF

echo "Starting App..."
# Run as ec2-user, not root
chown ec2-user:ec2-user /home/ec2-user/main.py
runuser -l ec2-user -c 'nohup uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir /home/ec2-user &'
echo "Setup Complete!"
""")


# Security group of our EC2 instances
def security_groups():
    try: 
        group = list(ec2.security_groups.filter(GroupNames=[SECURITY_GROUP_NAME]))

        if group: 
            sg = group[0]
            print(f"Security group {SECURITY_GROUP_NAME} already exists: {sg.id}")
            return sg.id
        
    except ec2_client.exceptions.ClientError as e:

        if 'InvalidGroup.NotFound' not in str(e): 
            raise e

    # if here - We need to create the group 

    security_group = ec2.create_security_group(
        Description='Allow traffic to EC2 instances',
        GroupName=SECURITY_GROUP_NAME
    )

    time.sleep(3)

    security_group.authorize_ingress(
        FromPort=8000,
        ToPort=8000,
        IpProtocol='tcp',
        CidrIp='0.0.0.0/0'
    )
    security_group.authorize_ingress(
        FromPort=22,
        ToPort=22,
        IpProtocol='tcp',
        CidrIp='0.0.0.0/0'
    )
    security_group.authorize_ingress(
        FromPort=80,
        ToPort=80,
        IpProtocol='tcp',
        CidrIp='0.0.0.0/0'
    )
    print(f'Security group created!')
    return security_group.id
        
def launch_ec2(flavor, tag, number_of_instances):
    '''Launch EC2 instances with the User data script'''
    # We can also use the run_instances with the Ec2 client
    instances = ec2.create_instances(
        ImageId='ami-085f043560da76e08',
        MinCount=number_of_instances,
        MaxCount=number_of_instances,
        InstanceType=flavor,
        KeyName=KEY,
        UserData=ec2_user_data,
        SecurityGroups=[SECURITY_GROUP_NAME],
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key' : 'Name',
                        'Value': tag
                    },
                    {
                        'Key': 'Project',
                        'Value': 'CustomELB'
                    }
                ]
            }
        ]
    )

    print('Waiting for instances to start ...')
    for i in instances: 
        i.wait_until_running()
        i.reload()
        print(f"Started {i.id} ({flavor}) at Public IP: {i.public_ip_address}")
    
    return instances

if __name__ == "__main__":
    sg_id = security_groups()

    # Launch 4 t3.small as I am using free tier AWS

    small_instances = launch_ec2('t3.small', 'Cluster1', 2)
    micro_instances = launch_ec2('t3.micro', 'Cluster2', 3)

    print('All instances launched, wait some minutes for user data script to start fastAPI.')
    print('You can test by accessing http://<public_ip>:8000 on each instance.')