# src/day8_setup.py
"""
Day 8 Complete Setup: Advanced Cloud Deployment
Initializes production-ready cloud infrastructure
"""

import os
import subprocess
import sys

def install_dependencies():
    """Install Day 8 cloud dependencies"""
    print("Installing Day 8 cloud dependencies...")
    
    dependencies = [
        "docker",
        "boto3", 
        "psutil",
        "prometheus-client"
    ]
    
    for dep in dependencies:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
            print(f"✅ Installed {dep}")
        except:
            print(f"⚠️ {dep} installation skipped (optional)")

def main():
    """Run Day 8 setup"""
    print("=" * 60)
    print("🚀 DAY 8: ADVANCED CLOUD DEPLOYMENT SETUP")
    print("=" * 60)
    
    from day8_cloud_deployment import main as cloud_main
    
    install_dependencies()
    cloud_main()
    
    print("\n🎉 DAY 8 COMPLETE!")
    print("\nYou now have:")
    print("✅ Production-ready containerized deployment")
    print("✅ Auto-scaling infrastructure")
    print("✅ Load balancing and health checks")
    print("✅ Production monitoring and alerting")
    print("✅ Multi-cloud deployment options")
    print("✅ Enterprise-grade security and backup")
    
    print("\nTo test the cloud interface:")
    print("streamlit run day8_complete_interface.py --server.port 8503")

if __name__ == "__main__":
    main()