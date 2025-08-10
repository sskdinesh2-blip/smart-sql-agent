"""
Smart SQL Pipeline Agent
Converts natural language requirements to production-ready SQL pipelines
"""
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SQLPipelineAgent:
    def __init__(self):
        """Initialize the SQL Pipeline Agent with OpenAI client"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found. Please check your .env file.")
        
        self.client = openai.OpenAI(api_key=api_key)
        
    def generate_pipeline(self, requirement, schema_info="", complexity="medium"):
        """Generate SQL pipeline from natural language requirement"""
        
        prompt = f"""
        Create a complete SQL data pipeline for this requirement:
        "{requirement}"
        
        Database schema: {schema_info if schema_info else "Standard e-commerce schema"}
        Complexity: {complexity}
        
        Provide:
        1. MAIN_QUERY: Primary SQL with CTEs and proper formatting
        2. VALIDATION: Data quality checks
        3. MONITORING: Performance metrics
        4. OPTIMIZATION: Performance tips
        
        Make it production-ready with comments.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a senior data engineer creating production SQL."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            return {
                "main_query": content,
                "validation": "-- Data quality checks included in main query",
                "monitoring": "-- Performance metrics to be added",
                "optimization": "-- Check indexes and query execution plan",
                "full_response": content
            }
            
        except Exception as e:
            return {
                "error": f"Failed to generate SQL: {str(e)}",
                "main_query": "",
                "validation": "",
                "monitoring": "",
                "optimization": "",
                "full_response": f"Error: {str(e)}"
            }

def test_agent():
    """Test the SQL agent"""
    print("🧪 Testing SQL Agent...")
    
    try:
        agent = SQLPipelineAgent()
        result = agent.generate_pipeline("Create a daily sales report by product category")
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print("✅ SQL Generated Successfully!")
            print(f"Preview: {result['main_query'][:200]}...")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        print("🔧 Make sure your .env file has a valid OPENAI_API_KEY")
        return None

if __name__ == "__main__":
    test_agent()