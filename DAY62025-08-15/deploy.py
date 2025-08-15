import subprocess
import time

def deploy():
    print("Starting deployment...")
    
    # Build Docker image
    subprocess.run(["docker", "build", "-t", "smart-sql-agent", "."])
    
    # Run container
    subprocess.run([
        "docker", "run", "-d", 
        "-p", "8000:8000", 
        "--name", "sql-agent-api",
        "smart-sql-agent"
    ])
    
    print("Waiting for startup...")
    time.sleep(10)
    
    # Test deployment
    import requests
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("Deployment successful!")
            print("API available at: http://localhost:8000")
        else:
            print("Deployment failed - health check failed")
    except:
        print("Deployment failed - API not responding")

if __name__ == "__main__":
    deploy()