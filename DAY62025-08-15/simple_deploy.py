# src/simple_deploy.py
import subprocess
import time
import requests

def deploy_without_docker():
    print("Starting local deployment...")
    
    # Just run the API server directly
    print("Starting API server...")
    api_process = subprocess.Popen([
        "python", "-m", "uvicorn", "api_server:app", 
        "--host", "0.0.0.0", "--port", "8000"
    ])
    
    print("Waiting for startup...")
    time.sleep(5)
    
    # Test the deployment
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("Deployment successful!")
            print("API available at: http://localhost:8000")
            print("API docs at: http://localhost:8000/docs")
            return api_process
        else:
            print("Deployment failed - health check failed")
    except:
        print("Deployment failed - API not responding")
    
    return api_process

if __name__ == "__main__":
    process = deploy_without_docker()
    print("Press Ctrl+C to stop the server")
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        print("Server stopped")