import boto3

REGION = 'ca-central-1'
TAG_CLUSTER_1 = {'Name': 'tag:Name', 'Values': ['Cluster1']}
TAG_CLUSTER_2 = {'Name': 'tag:Name', 'Values': ['Cluster2']}

ec2 = boto3.resource('ec2', region_name=REGION)
elbv2 = boto3.client('elbv2', region_name=REGION)

def get_default_vpc_and_subnets():
    """Auto-detects the default network to deploy the LB into."""
    client = boto3.client('ec2', region_name=REGION)
    vpcs = client.describe_vpcs(Filters=[{'Name': 'isDefault', 'Values': ['true']}])
    vpc_id = vpcs['Vpcs'][0]['VpcId']
    
    subnets = client.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    subnet_ids = [s['SubnetId'] for s in subnets['Subnets']]
    
    print(f"Detected Default VPC: {vpc_id}")
    return vpc_id, subnet_ids

def get_instance_ids(filters):
    """Finds running instances matching our tags."""
    filters.append({'Name': 'instance-state-name', 'Values': ['running']})
    instances = ec2.instances.filter(Filters=filters)
    return [i.id for i in instances]

def create_target_group(name, vpc_id):
    """Target group.
    Endpoint /cluster1 should redirect to instances in target group 1
    Endpoint /cluster2 should redirect to instances in target group 2
    """
    try:
        tg = elbv2.create_target_group(
            Name=name,
            Protocol='HTTP',
            Port=8000, # Our instances listen on 8000
            VpcId=vpc_id,
            TargetType='instance',
            HealthCheckProtocol='HTTP',
            HealthCheckPath='/' # The root path that returns "Instance is responding!"
        )
        arn = tg['TargetGroups'][0]['TargetGroupArn']
        print(f"Created Target Group: {name}")
        return arn
    except elbv2.exceptions.DuplicateTargetGroupNameException:
        print(f"Target Group {name} already exists. Fetching ARN...")
        tgs = elbv2.describe_target_groups(Names=[name])
        return tgs['TargetGroups'][0]['TargetGroupArn']

def register_targets(tg_arn, instance_ids):
    """Puts the instances into the bucket."""
    if not instance_ids:
        print("WARNING: No instances found to register!")
        return
        
    targets = [{'Id': i_id, 'Port': 8000} for i_id in instance_ids]
    elbv2.register_targets(TargetGroupArn=tg_arn, Targets=targets)
    print(f"Registered {len(instance_ids)} instances to {tg_arn.split('/')[-2]}")

def create_load_balancer(security_group_id, subnets):
    """Creates the main ALB entry point."""
    print("Creating Application Load Balancer...")
    lb = elbv2.create_load_balancer(
        Name='Assignment1-ALB',
        Subnets=subnets,
        SecurityGroups=[security_group_id],
        Scheme='internet-facing',
        Type='application',
        IpAddressType='ipv4'
    )
    lb_arn = lb['LoadBalancers'][0]['LoadBalancerArn']
    lb_dns = lb['LoadBalancers'][0]['DNSName']
    print(f"Load Balancer Created! DNS: {lb_dns}")
    return lb_arn, lb_dns

def create_listener_and_rules(lb_arn, tg1_arn, tg2_arn):
    """Sets up the traffic rules (The Logic)."""
    
    # 1. Create Listener (Port 80)
    # Default Action: Forward to Cluster 1 (Small) if no other rule matches
    listener = elbv2.create_listener(
        LoadBalancerArn=lb_arn,
        Protocol='HTTP',
        Port=80,
        DefaultActions=[{'Type': 'forward', 'TargetGroupArn': tg1_arn}]
    )
    listener_arn = listener['Listeners'][0]['ListenerArn']
    
    # 2. Rule for /cluster1 -> Target Group 1
    elbv2.create_rule(
        ListenerArn=listener_arn,
        Conditions=[{'Field': 'path-pattern', 'Values': ['/cluster1*']}],
        Priority=10,
        Actions=[{'Type': 'forward', 'TargetGroupArn': tg1_arn}]
    )
    
    # 3. Rule for /cluster2 -> Target Group 2
    elbv2.create_rule(
        ListenerArn=listener_arn,
        Conditions=[{'Field': 'path-pattern', 'Values': ['/cluster2*']}],
        Priority=20,
        Actions=[{'Type': 'forward', 'TargetGroupArn': tg2_arn}]
    )
    print("Routing Rules Created: /cluster1 -> Small, /cluster2 -> Micro")

if __name__ == "__main__":
    vpc_id, subnet_ids = get_default_vpc_and_subnets()
    
    # 1. Get Security Group ID (reusing the one from instance_manager)
    sg_res = boto3.client('ec2', region_name=REGION).describe_security_groups(GroupNames=['sec-group-asg1'])
    sg_id = sg_res['SecurityGroups'][0]['GroupId']

    # 2. Create Target Groups
    tg1_arn = create_target_group('TargetGroup-Small', vpc_id)
    tg2_arn = create_target_group('TargetGroup-Micro', vpc_id)
    
    # 3. Register Instances
    ids_small = get_instance_ids([TAG_CLUSTER_1])
    ids_micro = get_instance_ids([TAG_CLUSTER_2])
    
    register_targets(tg1_arn, ids_small)
    register_targets(tg2_arn, ids_micro)
    
    # 4. Create LB and Rules
    lb_arn, lb_dns = create_load_balancer(sg_id, subnet_ids)
    create_listener_and_rules(lb_arn, tg1_arn, tg2_arn)
    
    print("\n------------------------------------------------")
    print("SETUP COMPLETE!")
    print(f"Wait 2-3 minutes for the Load Balancer to 'Warm Up'.")
    print(f"Test URL 1: http://{lb_dns}/cluster1")
    print(f"Test URL 2: http://{lb_dns}/cluster2")
    print("------------------------------------------------")