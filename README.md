# AWS ELB From Scratch

A comprehensive AWS load balancing solution demonstrating multiple approaches to building scalable infrastructure on AWS. This project implements custom load balancers using Python, FastAPI, and AWS services, showcasing both Application Load Balancer (ALB) and custom application-level load balancing strategies.

## Project Overview

This is an learning project that demonstrates different load balancing architectures on AWS:

1. **Custom Application Load Balancer** - A FastAPI-based load balancer with active probing and latency-aware routing
2. **AWS ALB Integration** - Using AWS's managed Application Load Balancer with target groups and path-based routing
3. **Multi-Cluster Load Distribution** - Support for multiple instance clusters with different performance characteristics
4. **Performance Benchmarking** - Tools to measure and compare load balancer performance

## Features

- **Custom Load Balancer** (`custom_load_balancer.py`) - Latency-aware routing using active probing
- **AWS ALB Integration** (`aws_lb.py`) - Managed load balancing with target groups and health checks
- **Instance Manager** (`instance_manager.py`) - Automated EC2 instance provisioning and lifecycle management
- **Kill Switch Manager** (`kill_switch_manager.py`) - Emergency termination of all instances
- **Multi-Cluster Support** - Separate endpoints for Cluster 1 (Large) and Cluster 2 (Micro) instances
- **Performance Benchmarking** (`benchmark.py`) - Load testing with concurrent requests and latency measurements
- **Health Checks** - Automatic health endpoint monitoring on EC2 instances
- **Security Group Management** - Automated firewall configuration

## Architecture

The project consists of several integrated components:

### 1. Custom Load Balancer (`custom_load_balancer.py`)

A FastAPI-based application that implements intelligent load balancing:
- **Active Probing** - Continuously measures latency to each instance
- **Latency Scoreboard** - Tracks response times from all backend instances
- **Intelligent Routing** - Directs requests to the fastest responding instance
- **Multi-Cluster Support** - Routes `/cluster1` and `/cluster2` to respective instance groups
- **Dynamic Instance Discovery** - Automatically discovers and updates running instances from AWS

### 2. AWS ALB Integration (`aws_lb.py`)

Leverages AWS's managed Application Load Balancer service:
- **VPC Auto-Detection** - Automatically discovers default VPC and subnets
- **Target Groups** - Creates and manages target groups for each cluster
- **Path-Based Routing** - Routes `/cluster1` and `/cluster2` to appropriate target groups
- **Health Checks** - Integrated health monitoring on root endpoint
- **Dynamic Registration** - Registers running instances with target groups

### 3. Instance Manager (`instance_manager.py`)

Handles all EC2 instance lifecycle operations:
- **Security Group Setup** - Creates and configures firewall rules for instances
  - Opens port 8000 for application traffic
  - Opens port 22 for SSH access
- **Instance Launching** - Provisions EC2 instances with:
  - FastAPI web server for handling requests
  - Health check endpoints (`/`, `/cluster1`, `/cluster2`)
  - Automatic startup of the application via user data script
- **Multi-Flavor Support** - Launch instances with different types (t3.micro, t3.small, t3.medium, etc.)
- **Tagging System** - Organize instances by cluster (Cluster1, Cluster2)

### 4. Kill Switch Manager (`kill_switch_manager.py`)

Emergency termination utility:
- Identifies all instances tagged with project identifiers
- Gracefully terminates all instances
- Useful for cleanup and cost management

## Prerequisites

- AWS Account with proper IAM permissions (EC2, ELBv2, VPC)
- Python 3.8+
- Required Python packages: `boto3`, `fastapi`, `uvicorn`, `requests`, `aiohttp`
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
pip install boto3 fastapi uvicorn requests aiohttp
```

3. Configure AWS credentials:
```bash
aws configure
```

## Configuration

Before running, update the configuration in the Python files:

### Common Configuration
- `REGION` - AWS region (default: `ca-central-1`)
- `TAG_CLUSTER_1` - Tag filter for Cluster 1 instances (default: Name='Cluster1')
- `TAG_CLUSTER_2` - Tag filter for Cluster 2 instances (default: Name='Cluster2')

### In `instance_manager.py`:
- `SECURITY_GROUP_NAME` - Name for the security group
- `KEY` - Your EC2 key pair name
- `ImageId` - AMI ID (default: Amazon Linux 2)
- Instance type flavors (t3.micro, t3.small, t3.medium, etc.)

### In `benchmark.py`:
- `LB_BASE_URL` - Your load balancer DNS name or IP
- `NUM_REQUESTS` - Number of concurrent requests to send (default: 1000)

## Usage

### Step 1: Launch EC2 Instances

```python
from instance_manager import launch_ec2

# Launch 2 t3.medium instances for Cluster 1 (Large)
launch_ec2(flavor='t3.medium', tag='Cluster1', number_of_instances=2)

# Launch 3 t3.micro instances for Cluster 2 (Micro)
launch_ec2(flavor='t3.micro', tag='Cluster2', number_of_instances=3)
```

### Step 2: Option A - Use Custom Application Load Balancer

Start the custom load balancer (runs on port 8000 by default):

```bash
python custom_load_balancer.py
```

The load balancer will:
- Auto-discover instances in both clusters
- Continuously probe instances for latency measurements
- Route incoming requests to the fastest responding instance
- Serve endpoints:
  - `http://localhost:8000/cluster1` - Routes to Cluster 1 instances
  - `http://localhost:8000/cluster2` - Routes to Cluster 2 instances
  - `http://localhost:8000/` - Health check endpoint

### Step 2: Option B - Use AWS Application Load Balancer

```bash
python aws_lb.py
```

This will:
- Auto-detect your default VPC and subnets
- Create target groups for each cluster
- Create and configure an Application Load Balancer
- Register instances automatically
- Output the ALB DNS name for access

### Step 3: Benchmark Performance

```bash
# Update the LB_BASE_URL in benchmark.py first
python benchmark.py
```

The benchmark will:
- Send 1000 concurrent requests to `/cluster1`
- Send 1000 concurrent requests to `/cluster2`
- Measure total time and average latency per request
- Display performance metrics

### Step 4: Verify Instances

Check instance health from your load balancer:

```bash
curl http://localhost:8000/
curl http://localhost:8000/cluster1
curl http://localhost:8000/cluster2
```

Or for AWS ALB (replace with your DNS):

```bash
curl http://<your-alb-dns>/cluster1
curl http://<your-alb-dns>/cluster2
```

### Step 5: Terminate Instances

To shut down the entire infrastructure:

```bash
python kill_switch_manager.py
```

## Load Balancing Strategies

### Custom Load Balancer (Application-Level)

The custom load balancer uses **active probing** to measure instance latency:

1. **Latency Measurement** - Periodically sends requests to all instances and measures response time
2. **Scoreboard Update** - Maintains a real-time latency scoreboard for each instance
3. **Fastest-First Routing** - Always directs new requests to the instance with lowest latency
4. **Dead Instance Detection** - Marks unresponsive instances with high penalty scores

**Advantages:**
- Application-aware routing decisions
- No additional AWS service costs
- Customizable routing logic
- Real-time latency visibility

**Disadvantages:**
- Single point of failure (the LB itself)
- Additional network overhead from probing
- Limited to application layer

### AWS ALB (Managed Service)

Uses AWS's Application Load Balancer with path-based routing:

1. **Health Checks** - AWS performs automatic health checks on `/`
2. **Path-Based Routing** - Routes to target groups based on URL path
3. **Round-Robin Distribution** - Even distribution among healthy instances
4. **Auto-Scaling Ready** - Can integrate with auto-scaling groups

**Advantages:**
- AWS managed and highly available
- Automatic failover and recovery
- Integration with AWS ecosystem
- Native support for SSL/TLS termination

**Disadvantages:**
- Additional AWS costs
- Limited to predefined routing policies
- Less customization flexibility

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

### Completed Features
- ✅ Load balancing algorithm implementation (latency-aware routing)
- ✅ Health check monitoring and instance discovery
- ✅ Request routing logic with active probing
- ✅ AWS ALB integration with target groups and path-based routing
- ✅ Performance benchmarking with concurrent requests

### Future Enhancements
- [ ] Real-time metrics dashboard and visualization
- [ ] Auto-scaling integration based on load metrics
- [ ] Graceful instance shutdown with connection draining
- [ ] CloudWatch metrics and alarms integration
- [ ] Terraform/CloudFormation templates
- [ ] Docker containerization for load balancer
- [ ] WebSocket and sticky session support
- [ ] Advanced routing policies (weighted, geographic)
- [ ] Rate limiting and throttling
- [ ] Request/response caching

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