# src/api_server.py
"""
FastAPI REST API for Smart SQL Agent
Provides programmatic access to all system features
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio
import time
import json
from datetime import datetime
import sqlite3
import pandas as pd
import openai
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Smart SQL Agent API",
    description="Enterprise SQL generation and monitoring API",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class SQLGenerationRequest(BaseModel):
    requirement: str
    schema_info: Optional[str] = ""
    database_type: str = "sqlite"

class SQLExecutionRequest(BaseModel):
    sql: str
    database_config: Optional[Dict[str, Any]] = None

class PipelineScheduleRequest(BaseModel):
    name: str
    description: str
    requirement: str
    schedule_expression: str
    schedule_time: str
    database_config: Dict[str, Any]

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    components: Dict[str, str]
    metrics: Dict[str, Any]

# Global state for monitoring
monitoring_data = {
    "requests_count": 0,
    "error_count": 0,
    "start_time": datetime.now(),
    "last_request": None
}

class SQLAgent:
    """SQL Agent for API"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
    
    async def generate_sql(self, requirement: str, schema_info: str = "", database_type: str = "sqlite") -> Dict[str, Any]:
        """Generate SQL with AI or fallback"""
        
        start_time = time.time()
        
        try:
            if self.client:
                # AI Generation
                prompt = f"""
                Generate a SQL query for: {requirement}
                Schema: {schema_info}
                Database: {database_type}
                
                Provide clean, optimized SQL.
                """
                
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2
                )
                
                sql = response.choices[0].message.content
                method = "AI"
                
            else:
                # Fallback generation
                sql = self._generate_fallback_sql(requirement)
                method = "Fallback"
            
            generation_time = time.time() - start_time
            
            return {
                "success": True,
                "sql": sql,
                "generation_time": generation_time,
                "method": method,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sql": self._generate_fallback_sql(requirement),
                "generation_time": time.time() - start_time,
                "method": "Fallback",
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_fallback_sql(self, requirement: str) -> str:
        """Generate fallback SQL"""
        req_lower = requirement.lower()
        
        if any(word in req_lower for word in ['sales', 'revenue']):
            return """SELECT 
    c.name,
    SUM(o.amount) as total_revenue,
    COUNT(o.order_id) as order_count
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.name
ORDER BY total_revenue DESC;"""
        
        return "SELECT COUNT(*) as total_records FROM customers;"
    
    async def execute_sql(self, sql: str, database_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute SQL query"""
        
        start_time = time.time()
        
        try:
            # Use provided config or default to sample database
            if database_config and database_config.get("type") == "sqlite":
                db_path = database_config.get("database", "sample_data.db")
            else:
                db_path = "sample_data.db"
            
            conn = sqlite3.connect(db_path)
            df = pd.read_sql_query(sql, conn)
            conn.close()
            
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "data": df.to_dict('records'),
                "columns": df.columns.tolist(),
                "rows": len(df),
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }

# Initialize SQL Agent
sql_agent = SQLAgent()

# Middleware to track requests
@app.middleware("http")
async def track_requests(request, call_next):
    monitoring_data["requests_count"] += 1
    monitoring_data["last_request"] = datetime.now()
    
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        monitoring_data["error_count"] += 1
        raise

# API Endpoints

@app.get("/", response_model=Dict[str, str])
async def root():
    """API root endpoint"""
    return {
        "message": "Smart SQL Agent API",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """System health check"""
    
    uptime = datetime.now() - monitoring_data["start_time"]
    error_rate = (monitoring_data["error_count"] / max(monitoring_data["requests_count"], 1)) * 100
    
    return HealthResponse(
        status="healthy" if error_rate < 5 else "degraded",
        timestamp=datetime.now().isoformat(),
        components={
            "api_server": "operational",
            "sql_agent": "operational",
            "database": "connected"
        },
        metrics={
            "uptime_seconds": int(uptime.total_seconds()),
            "total_requests": monitoring_data["requests_count"],
            "error_count": monitoring_data["error_count"],
            "error_rate_percent": round(error_rate, 2),
            "last_request": monitoring_data["last_request"].isoformat() if monitoring_data["last_request"] else None
        }
    )

@app.post("/sql/generate")
async def generate_sql(request: SQLGenerationRequest):
    """Generate SQL from natural language requirement"""
    
    try:
        result = await sql_agent.generate_sql(
            requirement=request.requirement,
            schema_info=request.schema_info,
            database_type=request.database_type
        )
        return result
        
    except Exception as e:
        monitoring_data["error_count"] += 1
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sql/execute")
async def execute_sql(request: SQLExecutionRequest):
    """Execute SQL query"""
    
    try:
        result = await sql_agent.execute_sql(
            sql=request.sql,
            database_config=request.database_config
        )
        return result
        
    except Exception as e:
        monitoring_data["error_count"] += 1
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pipeline/generate-and-execute")
async def generate_and_execute(request: SQLGenerationRequest):
    """Generate and execute SQL in one call"""
    
    try:
        # Generate SQL
        generation_result = await sql_agent.generate_sql(
            requirement=request.requirement,
            schema_info=request.schema_info,
            database_type=request.database_type
        )
        
        if not generation_result["success"]:
            return generation_result
        
        # Execute SQL
        execution_result = await sql_agent.execute_sql(
            sql=generation_result["sql"]
        )
        
        # Combine results
        return {
            "generation": generation_result,
            "execution": execution_result,
            "success": generation_result["success"] and execution_result["success"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        monitoring_data["error_count"] += 1
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    
    uptime = datetime.now() - monitoring_data["start_time"]
    
    return {
        "uptime_seconds": int(uptime.total_seconds()),
        "total_requests": monitoring_data["requests_count"],
        "error_count": monitoring_data["error_count"],
        "error_rate_percent": (monitoring_data["error_count"] / max(monitoring_data["requests_count"], 1)) * 100,
        "requests_per_hour": monitoring_data["requests_count"] / max(uptime.total_seconds() / 3600, 1),
        "last_request": monitoring_data["last_request"].isoformat() if monitoring_data["last_request"] else None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/database/schema")
async def get_schema():
    """Get database schema information"""
    
    try:
        conn = sqlite3.connect("sample_data.db")
        cursor = conn.cursor()
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        schema = {}
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            schema[table_name] = [
                {
                    "name": col[1],
                    "type": col[2],
                    "nullable": not col[3],
                    "primary_key": bool(col[5])
                }
                for col in columns
            ]
        
        conn.close()
        
        return {
            "success": True,
            "schema": schema,
            "table_count": len(schema),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Background task example
@app.post("/pipeline/schedule")
async def schedule_pipeline(request: PipelineScheduleRequest, background_tasks: BackgroundTasks):
    """Schedule a pipeline for execution"""
    
    # This would integrate with your pipeline scheduler
    # For now, we'll simulate scheduling
    
    pipeline_id = f"pipeline_{int(time.time())}"
    
    # Add background task
    background_tasks.add_task(
        simulate_pipeline_execution,
        pipeline_id,
        request.requirement
    )
    
    return {
        "success": True,
        "pipeline_id": pipeline_id,
        "status": "scheduled",
        "message": f"Pipeline '{request.name}' scheduled successfully",
        "timestamp": datetime.now().isoformat()
    }

async def simulate_pipeline_execution(pipeline_id: str, requirement: str):
    """Simulate pipeline execution in background"""
    
    # Simulate some work
    await asyncio.sleep(2)
    
    # Generate and execute SQL
    result = await sql_agent.generate_sql(requirement)
    
    # Log result (in production, this would be stored in database)
    print(f"Pipeline {pipeline_id} completed: {result['success']}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)