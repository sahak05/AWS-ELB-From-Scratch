# AWS ELB From Scratch

A custom implementation of an AWS Elastic Load Balancer (ELB) built from the ground up using Python and AWS EC2 instances. This project demonstrates load balancing principles and infrastructure automation.

## Project Overview

This is a learning/implementation project that creates a custom load balancing solution using AWS EC2 instances instead of using AWS's managed ELB service. The project automates instance management, load balancing logic, and provides emergency termination capabilities through a kill switch mechanism.

## Features

- **Instance Manager** - Automated EC2 instance provisioning and management
- **Kill Switch Manager** - Emergency termination of all load balancer instances
- **Multi-Cluster Support** - Separate endpoints for different instance clusters (Large and Micro)
- **Health Checks** - Built-in health check endpoints on EC2 instances
- **Security Group Management** - Automated security group creation and configuration
- **Infrastructure as Code** - Complete automation using boto3

## Architecture

The project consists of two main components:

### 1. Instance Manager (`instance_manager.py`)

Handles all EC2 instance lifecycle operations:
- **Security Group Setup** - Creates and configures firewall rules for instances
  - Opens port 8000 for application traffic
  - Opens port 22 for SSH access
- **Instance Launching** - Provisions EC2 instances with:
  - FastAPI web server for handling requests
  - Health check endpoints (`/`, `/cluster1`, `/cluster2`)
  - Automatic startup of the application via user data script
- **Multi-Flavor Support** - Launch instances with different types (t3.micro, t3.small, t3.medium, etc.)
- **Tagging System** - Organize instances by tags for easy management

### 2. Kill Switch Manager (`kill_switch_manager.py`)

Emergency termination utility:
- Identifies all instances tagged with project identifier
- Gracefully terminates all instances
- Useful for cleanup and cost management

## Prerequisites

- AWS Account with proper IAM permissions
- Python 3.7+
- boto3 library
- AWS CLI configured with credentials
- EC2 key pair for SSH access

## Installation

1. Clone the repository:
```bash
git clone https://github.com/sahak05/AWS-ELB-From-Scratch.git
cd AWS-ELB-From-Scratch
```

2. Install dependencies:
```bash
pip install boto3
```

3. Configure AWS credentials:
```bash
aws configure
```

## Configuration

Before running, update the configuration in both Python files:

### In `instance_manager.py`:
- `REGION` - AWS region (default: `ca-central-1`)
- `SECURITY_GROUP_NAME` - Name for the security group
- `KEY` - Your EC2 key pair name
- `ImageId` - AMI ID (default: Amazon Linux 2)

### In `kill_switch_manager.py`:
- `REGION` - AWS region (must match instance_manager.py)
- Filter tags can be customized based on your tagging strategy

## Usage

### Launch EC2 Instances

```python
from instance_manager import launch_ec2

# Launch 2 t3.medium instances for Cluster 1
launch_ec2(flavor='t3.medium', tag='cluster-1-large', number_of_instances=2)

# Launch 3 t3.micro instances for Cluster 2
launch_ec2(flavor='t3.micro', tag='cluster-2-micro', number_of_instances=3)
```

### Verify Instance Health

Once instances are running, you can check their health:

```bash
curl http://<instance-public-ip>:8000/
curl http://<instance-public-ip>:8000/cluster1
curl http://<instance-public-ip>:8000/cluster2
```

### Terminate All Instances

To shut down the entire infrastructure:

```bash
python kill_switch_manager.py
```

## Application Endpoints

Each EC2 instance runs a FastAPI application with the following endpoints:

| Endpoint | Method | Response |
|----------|--------|----------|
| `/` | GET | General health check with instance hostname |
| `/cluster1` | GET | Cluster 1 (Large) specific response |
| `/cluster2` | GET | Cluster 2 (Micro) specific response |

## Security Considerations

- ⚠️ **SSH Security**: Change `CidrIp` from `0.0.0.0/0` to your specific IP range
- ⚠️ **Application Port**: Consider restricting port 8000 access to load balancer IPs
- 🔑 **Key Management**: Never commit your EC2 key pair to version control
- 🔐 **IAM Permissions**: Use minimal required IAM permissions

## Cost Optimization

- Use appropriate instance types (t3.micro for testing, t3.small/medium for production)
- Set up CloudWatch alarms for instance monitoring
- Regularly clean up using the kill switch manager
- Consider using spot instances for cost reduction

## Roadmap

- [ ] Load balancing algorithm implementation
- [ ] Health check monitoring and auto-scaling
- [ ] Metrics collection and monitoring dashboard
- [ ] Request routing logic
- [ ] Graceful instance shutdown
- [ ] Integration with CloudWatch
- [ ] Terraform/CloudFormation templates
- [ ] Docker containerization

## Troubleshooting

### Instances not launching
- Verify AWS credentials are configured correctly
- Check IAM permissions for EC2, VPC, and security groups
- Ensure the AMI ID is valid in your region
- Verify the key pair exists in your region

### Cannot connect to instances
- Check security group allows inbound traffic on ports 22 and 8000
- Verify you're using the correct key pair for SSH
- Ensure instances are in a running state (check AWS Console)

### Application not responding
- SSH into the instance and check FastAPI logs
- Verify port 8000 is open in the security group
- Check instance has internet access for pip install

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Author

- GitHub: [@sahak05](https://github.com/sahak05)