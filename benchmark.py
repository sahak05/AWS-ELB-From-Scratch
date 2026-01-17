import asyncio
import aiohttp
import time

# PASTE YOUR AWS LOAD BALANCER URL HERE (e.g., "http://Assignment1-ALB-123.ca-central-1.elb.amazonaws.com")
LB_BASE_URL = "http://YOUR_DNS_NAME_HERE" 

NUM_REQUESTS = 1000

async def call_endpoint_http(session, request_num, path):
    url = f"{LB_BASE_URL}{path}"
    try:
        async with session.get(url) as response:
            status_code = response.status
            # We read the text to ensure the request fully completed
            await response.text()
            if request_num % 100 == 0:
                print(f"Request {request_num}: Status {status_code}")
            return status_code
    except Exception as e:
        print(f"Request {request_num} Failed: {e}")
        return None

async def run_benchmark(cluster_path):
    print(f"\n--- Benchmarking {cluster_path} ({NUM_REQUESTS} requests) ---")
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(NUM_REQUESTS):
            tasks.append(call_endpoint_http(session, i, cluster_path))
        
        # Run all requests simultaneously
        await asyncio.gather(*tasks)

    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / NUM_REQUESTS
    
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average time per request: {avg_time:.4f} seconds")

if __name__ == "__main__":
    if "YOUR_DNS_NAME_HERE" in LB_BASE_URL:
        print("ERROR: Please update LB_BASE_URL with your Load Balancer DNS from the previous step.")
    else:
        # Benchmark Cluster 1 (Large Instances)
        asyncio.run(run_benchmark("/cluster1"))
        
        # Benchmark Cluster 2 (Micro Instances)
        asyncio.run(run_benchmark("/cluster2"))