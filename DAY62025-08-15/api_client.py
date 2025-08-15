import requests
import streamlit as st

class APIClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def generate_sql(self, requirement, schema_info=""):
        response = requests.post(
            f"{self.base_url}/sql/generate",
            json={
                "requirement": requirement,
                "schema_info": schema_info
            }
        )
        return response.json()
    
    def get_health(self):
        response = requests.get(f"{self.base_url}/health")
        return response.json()

# Test in Streamlit
if __name__ == "__main__":
    st.title("API Test")
    client = APIClient()
    
    if st.button("Test API"):
        health = client.get_health()
        st.json(health)
        
        result = client.generate_sql("Show top customers")
        st.json(result)