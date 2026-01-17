import boto3

# script to kill instances 

REGION = 'ca-central-1'
ec2 = boto3.resource('ec2', region_name=REGION)

def terminate_instances():

    print("Scanning for instances...")

    # Filter instances based on tag
    filter=[{'Name': 'tag:Project', 'Values': ['CustomELB']}]
    instances =  ec2.instances.filter(Filters=filter)

    print(f"Found {len(list(instances))} instances to terminate")

    instances.terminate()

    print("Termination sent. They will shut down soon....")

if __name__ == "__main__":
    terminate_instances()

