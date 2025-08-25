"""
Day 13 - Enterprise Integration & API Ecosystem Engine
Smart SQL Pipeline Generator - Enterprise Integration Platform

Fixed version with correct imports and error handling
"""

import asyncio
import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import hmac

try:
    from fastapi import FastAPI, HTTPException, Depends, Security, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import httpx
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    print("⚠️ FastAPI components not available - API server disabled")
    FASTAPI_AVAILABLE = False

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    print("⚠️ Redis not available - using memory-based rate limiting")
    REDIS_AVAILABLE = False

try:
    from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, Boolean
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, Session
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    print("⚠️ SQLAlchemy not available - using mock database")
    SQLALCHEMY_AVAILABLE = False


# Configuration and Models
class IntegrationType(str, Enum):
    WEBHOOK = "webhook"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    SSO = "sso"
    DATABASE = "database"
    KAFKA = "kafka"
    REDIS = "redis"


@dataclass
class IntegrationConfig:
    name: str
    integration_type: IntegrationType
    endpoint_url: str
    auth_config: Dict[str, Any]
    rate_limit: int = 1000
    retry_config: Dict[str, Any] = None
    webhook_secret: Optional[str] = None
    is_active: bool = True


# Pydantic models (only if FastAPI is available)
if FASTAPI_AVAILABLE:
    class APIKeyRequest(BaseModel):
        name: str
        permissions: List[str]
        expires_in_days: Optional[int] = 365
        rate_limit: int = 1000

    class WebhookRequest(BaseModel):
        url: str
        events: List[str]
        secret: Optional[str] = None
        headers: Dict[str, str] = {}

    class PipelineExecutionRequest(BaseModel):
        pipeline_id: str
        parameters: Dict[str, Any] = {}
        schedule: Optional[str] = None

    class IntegrationStatus(BaseModel):
        integration_id: str
        status: str
        last_ping: datetime
        error_count: int = 0
        success_count: int = 0


# Database Models (only if SQLAlchemy is available)
if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()

    class APIKey(Base):
        __tablename__ = "api_keys"
        
        id = Column(String, primary_key=True)
        name = Column(String, nullable=False)
        key_hash = Column(String, nullable=False)
        permissions = Column(Text)
        created_at = Column(DateTime, default=datetime.utcnow)
        expires_at = Column(DateTime)
        rate_limit = Column(Integer, default=1000)
        is_active = Column(Boolean, default=True)
        last_used = Column(DateTime)
        usage_count = Column(Integer, default=0)

    class Webhook(Base):
        __tablename__ = "webhooks"
        
        id = Column(String, primary_key=True)
        url = Column(String, nullable=False)
        events = Column(Text)
        secret = Column(String)
        headers = Column(Text)
        created_at = Column(DateTime, default=datetime.utcnow)
        is_active = Column(Boolean, default=True)
        success_count = Column(Integer, default=0)
        failure_count = Column(Integer, default=0)
        last_triggered = Column(DateTime)

    class Integration(Base):
        __tablename__ = "integrations"
        
        id = Column(String, primary_key=True)
        name = Column(String, nullable=False)
        integration_type = Column(String, nullable=False)
        config = Column(Text)
        created_at = Column(DateTime, default=datetime.utcnow)
        is_active = Column(Boolean, default=True)
        last_health_check = Column(DateTime)
        health_status = Column(String, default="unknown")


class EnterpriseIntegrationEngine:
    """
    Enterprise Integration Engine for Smart SQL Platform
    Handles API management, webhook systems, and external integrations
    """
    
    def __init__(self, database_url: str = "sqlite:///./smart_sql_integration.db", redis_url: str = "redis://localhost:6379"):
        # Initialize components based on availability
        self.sqlalchemy_available = SQLALCHEMY_AVAILABLE
        self.redis_available = REDIS_AVAILABLE
        
        # Database setup
        if self.sqlalchemy_available:
            try:
                self.engine = create_engine(database_url)
                self.SessionLocal = sessionmaker(bind=self.engine)
                Base.metadata.create_all(bind=self.engine)
                print("✅ Database initialized successfully")
            except Exception as e:
                print(f"⚠️ Database initialization failed: {e}")
                self.sqlalchemy_available = False
        
        # Redis setup
        if self.redis_available:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()  # Test connection
                print("✅ Redis connected successfully")
            except Exception as e:
                print(f"⚠️ Redis connection failed: {e}")
                self.redis_client = None
                self.redis_available = False
        
        # HTTP client setup
        try:
            self.http_client = httpx.AsyncClient()
            print("✅ HTTP client initialized")
        except Exception as e:
            print(f"⚠️ HTTP client initialization failed: {e}")
            self.http_client = None
        
        # Rate limiting
        self.rate_limiter = self._setup_rate_limiter()
        
        # Active integrations cache
        self.active_integrations: Dict[str, IntegrationConfig] = {}
        
        # Mock data for demo
        self.mock_api_keys = []
        self.mock_webhooks = []
        self.mock_integrations = []
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        print("🚀 Enterprise Integration Engine initialized!")

    def _setup_rate_limiter(self):
        """Setup rate limiter with fallback to memory"""
        class RateLimiter:
            def __init__(self, redis_client, redis_available):
                self.redis = redis_client
                self.redis_available = redis_available
                self.memory_store = {}
            
            async def is_allowed(self, key: str, limit: int, window: int = 3600):
                """Check if request is within rate limit"""
                if not self.redis_available:
                    # Memory-based fallback
                    current_time = datetime.utcnow().timestamp()
                    if key not in self.memory_store:
                        self.memory_store[key] = []
                    
                    # Clean old entries
                    self.memory_store[key] = [
                        t for t in self.memory_store[key] 
                        if current_time - t < window
                    ]
                    
                    if len(self.memory_store[key]) < limit:
                        self.memory_store[key].append(current_time)
                        return True
                    return False
                
                try:
                    # Redis-based rate limiting
                    current_time = int(datetime.utcnow().timestamp())
                    window_start = current_time - window
                    
                    pipe = self.redis.pipeline()
                    pipe.zremrangebyscore(key, 0, window_start)
                    pipe.zcard(key)
                    pipe.zadd(key, {str(current_time): current_time})
                    pipe.expire(key, window)
                    
                    results = pipe.execute()
                    current_count = results[1]
                    
                    return current_count < limit
                except Exception:
                    # Fallback to memory if Redis fails
                    return await self.is_allowed(key, limit, window)
        
        return RateLimiter(self.redis_client if self.redis_available else None, self.redis_available)

    def generate_api_key(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate new API key with permissions"""
        try:
            api_key = f"sql_{secrets.token_urlsafe(32)}"
            key_id = secrets.token_urlsafe(16)
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            expires_at = None
            expires_in_days = request_data.get('expires_in_days')
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
            api_key_data = {
                "id": key_id,
                "name": request_data.get('name', 'Unnamed Key'),
                "key_hash": key_hash,
                "permissions": request_data.get('permissions', []),
                "expires_at": expires_at,
                "rate_limit": request_data.get('rate_limit', 1000),
                "created_at": datetime.utcnow(),
                "is_active": True,
                "usage_count": 0
            }
            
            if self.sqlalchemy_available:
                try:
                    db_key = APIKey(
                        id=key_id,
                        name=api_key_data['name'],
                        key_hash=key_hash,
                        permissions=json.dumps(api_key_data['permissions']),
                        expires_at=expires_at,
                        rate_limit=api_key_data['rate_limit']
                    )
                    
                    with self.SessionLocal() as session:
                        session.add(db_key)
                        session.commit()
                        print("✅ API key saved to database")
                except Exception as e:
                    print(f"⚠️ Database save failed, using mock storage: {e}")
                    self.mock_api_keys.append(api_key_data)
            else:
                self.mock_api_keys.append(api_key_data)
            
            return {
                "api_key": api_key,
                "key_id": key_id,
                "permissions": api_key_data['permissions'],
                "rate_limit": api_key_data['rate_limit'],
                "expires_at": expires_at.isoformat() if expires_at else None,
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"Error generating API key: {e}")
            return {"error": "Failed to generate API key", "details": str(e)}

    def create_webhook(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new webhook endpoint"""
        try:
            webhook_id = f"wh_{secrets.token_urlsafe(12)}"
            webhook_secret = request_data.get('secret') or secrets.token_urlsafe(32)
            
            webhook_data = {
                "id": webhook_id,
                "url": request_data.get('url'),
                "events": request_data.get('events', []),
                "secret": webhook_secret,
                "headers": request_data.get('headers', {}),
                "created_at": datetime.utcnow(),
                "is_active": True,
                "success_count": 0,
                "failure_count": 0
            }
            
            if self.sqlalchemy_available:
                try:
                    webhook = Webhook(
                        id=webhook_id,
                        url=webhook_data['url'],
                        events=json.dumps(webhook_data['events']),
                        secret=webhook_secret,
                        headers=json.dumps(webhook_data['headers'])
                    )
                    
                    with self.SessionLocal() as session:
                        session.add(webhook)
                        session.commit()
                        print("✅ Webhook saved to database")
                except Exception as e:
                    print(f"⚠️ Database save failed, using mock storage: {e}")
                    self.mock_webhooks.append(webhook_data)
            else:
                self.mock_webhooks.append(webhook_data)
            
            return {
                "webhook_id": webhook_id,
                "url": webhook_data['url'],
                "events": webhook_data['events'],
                "secret": webhook_secret,
                "status": "success"
            }
            
        except Exception as e:
            self.logger.error(f"Error creating webhook: {e}")
            return {"error": "Failed to create webhook", "details": str(e)}

    def register_integration(self, config: IntegrationConfig) -> str:
        """Register external system integration"""
        try:
            integration_id = f"int_{secrets.token_urlsafe(12)}"
            
            integration_data = {
                "id": integration_id,
                "name": config.name,
                "integration_type": config.integration_type.value,
                "config": asdict(config),
                "created_at": datetime.utcnow(),
                "is_active": True,
                "health_status": "unknown"
            }
            
            if self.sqlalchemy_available:
                try:
                    integration = Integration(
                        id=integration_id,
                        name=config.name,
                        integration_type=config.integration_type.value,
                        config=json.dumps(asdict(config))
                    )
                    
                    with self.SessionLocal() as session:
                        session.add(integration)
                        session.commit()
                        print("✅ Integration saved to database")
                except Exception as e:
                    print(f"⚠️ Database save failed, using mock storage: {e}")
                    self.mock_integrations.append(integration_data)
            else:
                self.mock_integrations.append(integration_data)
            
            # Cache active integration
            self.active_integrations[integration_id] = config
            
            return integration_id
            
        except Exception as e:
            self.logger.error(f"Error registering integration: {e}")
            return f"error_{secrets.token_urlsafe(8)}"

    def get_integration_stats(self) -> Dict[str, Any]:
        """Get integration platform statistics"""
        try:
            if self.sqlalchemy_available:
                try:
                    with self.SessionLocal() as session:
                        api_key_count = session.query(APIKey).filter(APIKey.is_active == True).count()
                        webhook_count = session.query(Webhook).filter(Webhook.is_active == True).count()
                        integration_count = session.query(Integration).filter(Integration.is_active == True).count()
                except Exception:
                    # Fallback to mock data
                    api_key_count = len([k for k in self.mock_api_keys if k.get('is_active', True)])
                    webhook_count = len([w for w in self.mock_webhooks if w.get('is_active', True)])
                    integration_count = len([i for i in self.mock_integrations if i.get('is_active', True)])
            else:
                # Use mock data
                api_key_count = len([k for k in self.mock_api_keys if k.get('is_active', True)])
                webhook_count = len([w for w in self.mock_webhooks if w.get('is_active', True)])
                integration_count = len([i for i in self.mock_integrations if i.get('is_active', True)])
            
            return {
                "api_keys": {"total_active": api_key_count},
                "webhooks": {"total_active": webhook_count},
                "integrations": {"total_active": integration_count},
                "system_status": {
                    "database": "connected" if self.sqlalchemy_available else "mock",
                    "redis": "connected" if self.redis_available else "memory",
                    "http_client": "available" if self.http_client else "unavailable"
                },
                "last_updated": datetime.utcnow().isoformat()
            }
                
        except Exception as e:
            self.logger.error(f"Error getting integration stats: {e}")
            return {"error": "Failed to retrieve stats", "details": str(e)}


# FastAPI Application Setup (only if FastAPI is available)
def create_integration_api(engine: EnterpriseIntegrationEngine) -> FastAPI:
    """Create FastAPI application with integration endpoints"""
    
    if not FASTAPI_AVAILABLE:
        print("❌ FastAPI not available - API server cannot start")
        return None
    
    app = FastAPI(
        title="Smart SQL - Enterprise Integration API",
        description="Enterprise integration platform for Smart SQL Pipeline Generator",
        version="1.0.0"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.post("/api/v1/auth/api-keys")
    async def create_api_key(request: APIKeyRequest):
        """Create new API key"""
        request_data = {
            "name": request.name,
            "permissions": request.permissions,
            "expires_in_days": request.expires_in_days,
            "rate_limit": request.rate_limit
        }
        return engine.generate_api_key(request_data)
    
    @app.post("/api/v1/webhooks")
    async def create_webhook(request: WebhookRequest):
        """Create new webhook"""
        request_data = {
            "url": request.url,
            "events": request.events,
            "secret": request.secret,
            "headers": request.headers
        }
        return engine.create_webhook(request_data)
    
    @app.get("/api/v1/stats")
    async def get_stats():
        """Get integration platform statistics"""
        return engine.get_integration_stats()
    
    @app.get("/api/v1/health")
    async def health_check():
        """API health check"""
        return {
            "status": "healthy", 
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "fastapi": True,
                "database": engine.sqlalchemy_available,
                "redis": engine.redis_available,
                "http_client": engine.http_client is not None
            }
        }
    
    return app


# Main function for testing and development
async def main():
    """Main function for testing and development"""
    
    print("🚀 Smart SQL Enterprise Integration Engine")
    print("=" * 50)
    
    # Initialize engine
    engine = EnterpriseIntegrationEngine()
    
    # Test API key generation
    print("\n📋 Testing API Key Generation...")
    api_key_request = {
        "name": "Test Integration",
        "permissions": ["pipeline:execute", "webhook:create"],
        "rate_limit": 500,
        "expires_in_days": 30
    }
    api_key_result = engine.generate_api_key(api_key_request)
    if "error" not in api_key_result:
        print(f"✅ Generated API Key: {api_key_result['api_key'][:20]}...")
    else:
        print(f"❌ API Key generation failed: {api_key_result['error']}")
    
    # Test webhook creation
    print("\n🔗 Testing Webhook Creation...")
    webhook_request = {
        "url": "https://api.example.com/webhook",
        "events": ["pipeline.completed", "pipeline.failed"],
        "headers": {"Authorization": "Bearer token123"}
    }
    webhook_result = engine.create_webhook(webhook_request)
    if "error" not in webhook_result:
        print(f"✅ Created Webhook: {webhook_result['webhook_id']}")
    else:
        print(f"❌ Webhook creation failed: {webhook_result['error']}")
    
    # Test integration registration
    print("\n🔧 Testing Integration Registration...")
    integration_config = IntegrationConfig(
        name="PostgreSQL Production",
        integration_type=IntegrationType.DATABASE,
        endpoint_url="postgresql://localhost:5432/production",
        auth_config={"username": "admin", "password": "secure"},
        rate_limit=2000
    )
    integration_id = engine.register_integration(integration_config)
    print(f"✅ Registered Integration: {integration_id}")
    
    # Get platform stats
    print("\n📊 Platform Statistics...")
    stats = engine.get_integration_stats()
    print(json.dumps(stats, indent=2))
    
    print("\n✅ Enterprise Integration Engine Ready!")
    if FASTAPI_AVAILABLE:
        print("🚀 To start API server: python day13_integration_engine.py")
        print("📚 API Documentation: http://localhost:8000/docs")
    else:
        print("⚠️ Install FastAPI to enable API server: pip install fastapi uvicorn")


if __name__ == "__main__":
    if FASTAPI_AVAILABLE:
        # Create and run FastAPI app
        integration_engine = EnterpriseIntegrationEngine()
        app = create_integration_api(integration_engine)
        
        if app:
            print("🌐 Starting FastAPI server...")
            print("📊 Dashboard: http://localhost:8501")
            print("🔗 API Docs: http://localhost:8000/docs")
            print("📋 API Base: http://localhost:8000/api/v1")
            uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
        else:
            print("❌ Cannot start API server")
    else:
        # Run basic tests
        asyncio.run(main())