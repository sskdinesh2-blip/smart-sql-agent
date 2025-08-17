# src/enhanced_api_server.py
"""
Enhanced API Server with Multi-User Authentication
Combines all previous API features with user management and team collaboration
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from datetime import datetime, timedelta
import time
import sqlite3
import asyncio
from typing import List, Optional, Dict

# Import our authentication system
from auth_system import (
    auth_system, get_current_user, require_role, 
    User, UserCreate, UserLogin, Token
)
from team_collaboration import TeamCollaboration, Project, SharedQuery, Comment

app = FastAPI(
    title="Smart SQL Agent Pro API",
    description="Multi-user SQL generation platform with team collaboration",
    version="2.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize systems
collaboration = TeamCollaboration()

# Pydantic models for API requests
class SQLGenerationRequest(BaseModel):
    requirement: str
    schema_info: Optional[str] = ""
    project_id: Optional[int] = None

class ProjectRequest(BaseModel):
    name: str
    description: str
    team_members: Optional[List[int]] = []

class QueryShareRequest(BaseModel):
    title: str
    sql_query: str
    description: str
    project_id: Optional[int] = None
    tags: Optional[List[str]] = []
    is_public: bool = False

class CommentRequest(BaseModel):
    content: str
    query_id: int

# System metrics
system_metrics = {
    "start_time": time.time(),
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "active_users": 0
}

@app.middleware("http")
async def track_requests(request, call_next):
    """Track API usage metrics"""
    system_metrics["total_requests"] += 1
    start_time = time.time()
    
    try:
        response = await call_next(request)
        system_metrics["successful_requests"] += 1
        return response
    except Exception as e:
        system_metrics["failed_requests"] += 1
        raise e
    finally:
        # Log request time (could be used for monitoring)
        request_time = time.time() - start_time

# Authentication endpoints
@app.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    """Register new user"""
    try:
        user = auth_system.create_user(user_data)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    """Authenticate user and return token"""
    user = auth_system.authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = auth_system.create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user
    )

@app.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@app.get("/auth/users", response_model=List[User])
async def get_all_users(current_user: User = Depends(require_role("admin"))):
    """Get all users (admin only)"""
    return auth_system.get_all_users()

# SQL Generation endpoints (protected)
@app.post("/sql/generate")
async def generate_sql(
    request: SQLGenerationRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate SQL from natural language requirement"""
    start_time = time.time()
    
    try:
        # Mock SQL generation (replace with your actual AI agent)
        mock_sql = f"""
-- Generated SQL for: {request.requirement}
-- User: {current_user.username}
-- Generated at: {datetime.now().isoformat()}

SELECT 
    c.customer_name,
    SUM(o.order_amount) as total_revenue,
    COUNT(o.order_id) as order_count
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
{f"-- Schema context: {request.schema_info}" if request.schema_info else ""}
GROUP BY c.customer_id, c.customer_name
ORDER BY total_revenue DESC
LIMIT 10;
        """.strip()
        
        generation_time = time.time() - start_time
        
        result = {
            "success": True,
            "sql": mock_sql,
            "generation_time": round(generation_time, 3),
            "method": "AI Enhanced",
            "user_id": current_user.id,
            "project_id": request.project_id,
            "timestamp": datetime.now().isoformat()
        }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQL generation failed: {str(e)}")

# Team collaboration endpoints
@app.post("/projects", response_model=dict)
async def create_project(
    project_request: ProjectRequest,
    current_user: User = Depends(get_current_user)
):
    """Create new team project"""
    project = Project(
        name=project_request.name,
        description=project_request.description,
        owner_id=current_user.id,
        team_members=project_request.team_members + [current_user.id]
    )
    
    project_id = collaboration.create_project(project)
    return {"success": True, "project_id": project_id}

@app.get("/projects", response_model=List[dict])
async def get_user_projects(current_user: User = Depends(get_current_user)):
    """Get user's projects"""
    projects = collaboration.get_user_projects(current_user.id)
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "owner_id": p.owner_id,
            "team_members": p.team_members,
            "status": p.status,
            "created_at": p.created_at
        }
        for p in projects
    ]

@app.post("/queries/share", response_model=dict)
async def share_query(
    query_request: QueryShareRequest,
    current_user: User = Depends(get_current_user)
):
    """Share SQL query with team"""
    shared_query = SharedQuery(
        title=query_request.title,
        sql_query=query_request.sql_query,
        description=query_request.description,
        project_id=query_request.project_id,
        created_by=current_user.id,
        tags=query_request.tags,
        is_public=query_request.is_public
    )
    
    query_id = collaboration.share_query(shared_query)
    return {"success": True, "query_id": query_id}

@app.get("/queries/shared", response_model=List[dict])
async def get_shared_queries(
    project_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """Get shared queries"""
    queries = collaboration.get_shared_queries(current_user.id, project_id)
    return [
        {
            "id": q.id,
            "title": q.title,
            "sql_query": q.sql_query,
            "description": q.description,
            "project_id": q.project_id,
            "created_by": q.created_by,
            "tags": q.tags,
            "is_public": q.is_public,
            "execution_count": q.execution_count,
            "created_at": q.created_at
        }
        for q in queries
    ]

@app.post("/queries/{query_id}/comments", response_model=dict)
async def add_comment(
    query_id: int,
    comment_request: CommentRequest,
    current_user: User = Depends(get_current_user)
):
    """Add comment to shared query"""
    comment = Comment(
        content=comment_request.content,
        query_id=query_id,
        user_id=current_user.id,
        username=current_user.username
    )
    
    comment_id = collaboration.add_comment(comment)
    return {"success": True, "comment_id": comment_id}

@app.get("/queries/{query_id}/comments", response_model=List[dict])
async def get_query_comments(query_id: int, current_user: User = Depends(get_current_user)):
    """Get comments for query"""
    comments = collaboration.get_query_comments(query_id)
    return [
        {
            "id": c.id,
            "content": c.content,
            "user_id": c.user_id,
            "username": c.username,
            "created_at": c.created_at
        }
        for c in comments
    ]

# Analytics endpoints
@app.get("/analytics/team")
async def get_team_analytics(
    project_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """Get team collaboration analytics"""
    return collaboration.get_team_analytics(project_id)

@app.get("/analytics/user")
async def get_user_analytics(current_user: User = Depends(get_current_user)):
    """Get user-specific analytics"""
    queries = collaboration.get_shared_queries(current_user.id)
    user_queries = [q for q in queries if q.created_by == current_user.id]
    
    return {
        "queries_shared": len(user_queries),
        "total_executions": sum(q.execution_count for q in user_queries),
        "public_queries": len([q for q in user_queries if q.is_public]),
        "recent_activity": [
            {
                "title": q.title,
                "executions": q.execution_count,
                "created_at": q.created_at
            }
            for q in user_queries[:5]
        ]
    }

# System monitoring endpoints
@app.get("/health")
async def health_check():
    """System health status"""
    uptime = time.time() - system_metrics["start_time"]
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "features": ["multi-user", "team-collaboration", "authentication"],
        "metrics": {
            "uptime_seconds": round(uptime, 2),
            "uptime_formatted": str(timedelta(seconds=int(uptime))),
            "total_requests": system_metrics["total_requests"],
            "success_rate": round(
                system_metrics["successful_requests"] / max(system_metrics["total_requests"], 1) * 100, 2
            ),
            "active_users": len(auth_system.get_all_users())
        }
    }

@app.get("/metrics")
async def get_system_metrics(current_user: User = Depends(require_role("admin"))):
    """Detailed system metrics (admin only)"""
    uptime = time.time() - system_metrics["start_time"]
    total_requests = system_metrics["total_requests"]
    
    return {
        "system": {
            "uptime_seconds": round(uptime, 2),
            "total_requests": total_requests,
            "successful_requests": system_metrics["successful_requests"],
            "failed_requests": system_metrics["failed_requests"],
            "success_rate_percent": round(
                system_metrics["successful_requests"] / max(total_requests, 1) * 100, 2
            ),
            "error_rate_percent": round(
                system_metrics["failed_requests"] / max(total_requests, 1) * 100, 2
            )
        },
        "collaboration": collaboration.get_team_analytics(),
        "users": {
            "total_users": len(auth_system.get_all_users()),
            "admin_users": len([u for u in auth_system.get_all_users() if u.role == "admin"]),
            "active_users": len([u for u in auth_system.get_all_users() if u.is_active])
        }
    }

@app.get("/")
async def root():
    """API information"""
    return {
        "service": "Smart SQL Agent Pro API",
        "version": "2.0.0",
        "features": [
            "Multi-user authentication",
            "Team collaboration",
            "SQL query sharing",
            "Project management",
            "Real-time analytics",
            "Production monitoring"
        ],
        "endpoints": {
            "authentication": ["/auth/register", "/auth/login", "/auth/me"],
            "sql_generation": ["/sql/generate"],
            "collaboration": ["/projects", "/queries/share", "/queries/shared"],
            "analytics": ["/analytics/team", "/analytics/user"],
            "monitoring": ["/health", "/metrics"]
        },
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("enhanced_api_server:app", host="0.0.0.0", port=8000, reload=True)