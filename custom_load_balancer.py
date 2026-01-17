import boto3
import requests
import time
import uvicorn
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

REGION = 'ca-central-1'
TAG_CLUSTER_1 = {'Name': 'tag:Name', 'Values': ['Cluster1']}
TAG_CLUSTER_2 = {'Name': 'tag:Name', 'Values': ['Cluster2']}

# Global "Scoreboard" to store which instance is fastest
# Format: { "1.2.3.4": 0.05, "5.6.7.8": 0.20 }
latency_scoreboard = {}
cluster1_ips = []
cluster2_ips = []

def get_instance_ips(filters):
    """Asks AWS for the IPs of our running instances."""
    ec2 = boto3.resource('ec2', region_name=REGION)
    filters.append({'Name': 'instance-state-name', 'Values': ['running']})
    instances = ec2.instances.filter(Filters=filters)
    return [i.public_ip_address for i in instances if i.public_ip_address]

def update_scoreboard():
    """
    ACTIVE PROBING:
    Pings every instance to see how fast it answers.
    Updates the global 'latency_scoreboard'.
    """
    all_ips = cluster1_ips + cluster2_ips
    print(f"\n--- Active Probing {len(all_ips)} instances ---")
    
    for ip in all_ips:
        try:
            start = time.time()
            # We assume every instance has /cluster1 or /cluster2. 
            # We just hit the root / to test connectivity.
            requests.get(f"http://{ip}:8000/", timeout=2)
            latency = time.time() - start
            
            latency_scoreboard[ip] = latency
            print(f"Instance {ip}: {latency:.4f}s")
        except:
            # If it fails, give it a huge penalty score so we don't use it
            latency_scoreboard[ip] = 999.0
            print(f"Instance {ip}: DEAD")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Startup: Find IPs
    global cluster1_ips, cluster2_ips
    print("Finding Instances...")
    cluster1_ips = get_instance_ips([TAG_CLUSTER_1])
    cluster2_ips = get_instance_ips([TAG_CLUSTER_2])
    
    if not cluster1_ips:
        print("ERROR: No instances found. Did you run the Factory?")
    
    # 2. Initial Health Check
    update_scoreboard()
    
    yield # App runs here
    
    # 3. Shutdown
    print("Shutting down load balancer.")

app = FastAPI(lifespan=lifespan)

def get_fastest_instance(pool_ips):
    """The Logic: Pick the IP with the lowest latency score."""
    # 1. Filter scoreboard to only include IPs in this pool
    candidates = {ip: latency_scoreboard.get(ip, 999) for ip in pool_ips}
    
    # 2. Find the minimum value (fastest time)
    best_ip = min(candidates, key=candidates.get)
    
    if candidates[best_ip] >= 999:
        raise HTTPException(status_code=503, detail="No healthy instances available")
        
    return best_ip

@app.get("/cluster1")
def proxy_cluster1():
    """Route traffic to the fastest Small instance"""
    # 1. Decision
    target_ip = get_fastest_instance(cluster1_ips)
    
    # 2. Forwarding (Proxy)
    try:
        resp = requests.get(f"http://{target_ip}:8000/cluster1")
        return resp.json()
    except:
        return {"error": "Failed to connect to worker"}

@app.get("/cluster2")
def proxy_cluster2():
    """Route traffic to the fastest Micro instance"""
    target_ip = get_fastest_instance(cluster2_ips)
    try:
        resp = requests.get(f"http://{target_ip}:8000/cluster2")
        return resp.json()
    except:
        return {"error": "Failed to connect to worker"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)

