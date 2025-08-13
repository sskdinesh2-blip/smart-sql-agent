"""
Configuration Manager for Smart SQL Pipeline Generator
Handles environment configuration, secrets, and deployment settings
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

@dataclass
class DatabaseConfig:
    type: str = "sqlite"
    host: Optional[str] = None
    port: Optional[int] = None
    database: str = "smart_sql_agent"
    username: Optional[str] = None
    password: Optional[str] = None
    ssl_mode: str = "prefer"
    pool_size: int = 5
    max_overflow: int = 10

@dataclass
class APIConfig:
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    rate_limit: int = 100
    timeout: int = 30
    max_retries: int = 3

@dataclass
class AppConfig:
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    host: str = "localhost"
    port: int = 8501
    secret_key: str = "dev-secret-key"
    log_level: str = "INFO"
    max_upload_size: int = 50  # MB

@dataclass
class SecurityConfig:
    enable_auth: bool = False
    session_timeout: int = 3600
    cors_origins: list = None
    api_keys_enabled: bool = False
    rate_limiting: bool = True

@dataclass
class MonitoringConfig:
    enable_metrics: bool = True
    log_queries: bool = True
    performance_tracking: bool = True
    error_reporting: bool = True
    health_check_interval: int = 60

class ConfigManager:
    def __init__(self, config_file: str = None, env_file: str = ".env"):
        self.config_file = config_file
        self.env_file = env_file
        self.logger = self._setup_logging()
        
        # Load configuration
        self._load_environment_variables()
        self.database = self._load_database_config()
        self.api = self._load_api_config()
        self.app = self._load_app_config()
        self.security = self._load_security_config()
        self.monitoring = self._load_monitoring_config()
        
        # Validate configuration
        self._validate_config()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for configuration manager"""
        logger = logging.getLogger('ConfigManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_environment_variables(self):
        """Load environment variables from .env file"""
        env_path = Path(self.env_file)
        
        if env_path.exists():
            try:
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            # Remove quotes if present
                            value = value.strip('\'"')
                            os.environ[key.strip()] = value
                
                self.logger.info(f"Loaded environment variables from {env_path}")
            except Exception as e:
                self.logger.warning(f"Failed to load .env file: {e}")
        else:
            self.logger.info("No .env file found, using system environment variables")
    
    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration"""
        
        # Check for DATABASE_URL (common in cloud deployments)
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            return self._parse_database_url(database_url)
        
        # Individual environment variables
        return DatabaseConfig(
            type=os.getenv('DB_TYPE', 'sqlite'),
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT', 5432)) if os.getenv('DB_PORT') else None,
            database=os.getenv('DB_NAME', 'smart_sql_agent'),
            username=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            ssl_mode=os.getenv('DB_SSL_MODE', 'prefer'),
            pool_size=int(os.getenv('DB_POOL_SIZE', 5)),
            max_overflow=int(os.getenv('DB_MAX_OVERFLOW', 10))
        )
    
    def _parse_database_url(self, url: str) -> DatabaseConfig:
        """Parse database URL format"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            
            db_type = "postgresql" if parsed.scheme.startswith('postgres') else parsed.scheme
            
            return DatabaseConfig(
                type=db_type,
                host=parsed.hostname,
                port=parsed.port,
                database=parsed.path.lstrip('/') if parsed.path else 'smart_sql_agent',
                username=parsed.username,
                password=parsed.password,
                ssl_mode='require' if parsed.scheme.startswith('postgres') else 'prefer'
            )
        except Exception as e:
            self.logger.error(f"Failed to parse DATABASE_URL: {e}")
            return DatabaseConfig()  # Return default config
    
    def _load_api_config(self) -> APIConfig:
        """Load API configuration"""
        return APIConfig(
            openai_api_key=os.getenv('OPENAI_API_KEY', ''),
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY', ''),
            rate_limit=int(os.getenv('API_RATE_LIMIT', 100)),
            timeout=int(os.getenv('API_TIMEOUT', 30)),
            max_retries=int(os.getenv('API_MAX_RETRIES', 3))
        )
    
    def _load_app_config(self) -> AppConfig:
        """Load application configuration"""
        env_name = os.getenv('ENVIRONMENT', 'development').lower()
        
        try:
            environment = Environment(env_name)
        except ValueError:
            environment = Environment.DEVELOPMENT
            self.logger.warning(f"Invalid environment '{env_name}', using development")
        
        return AppConfig(
            environment=environment,
            debug=os.getenv('DEBUG', 'true').lower() == 'true',
            host=os.getenv('HOST', 'localhost'),
            port=int(os.getenv('PORT', 8501)),
            secret_key=os.getenv('SECRET_KEY', 'dev-secret-key'),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            max_upload_size=int(os.getenv('MAX_UPLOAD_SIZE', 50))
        )
    
    def _load_security_config(self) -> SecurityConfig:
        """Load security configuration"""
        cors_origins = os.getenv('CORS_ORIGINS', '').split(',') if os.getenv('CORS_ORIGINS') else ['*']
        
        return SecurityConfig(
            enable_auth=os.getenv('ENABLE_AUTH', 'false').lower() == 'true',
            session_timeout=int(os.getenv('SESSION_TIMEOUT', 3600)),
            cors_origins=cors_origins,
            api_keys_enabled=os.getenv('API_KEYS_ENABLED', 'false').lower() == 'true',
            rate_limiting=os.getenv('RATE_LIMITING', 'true').lower() == 'true'
        )
    
    def _load_monitoring_config(self) -> MonitoringConfig:
        """Load monitoring configuration"""
        return MonitoringConfig(
            enable_metrics=os.getenv('ENABLE_METRICS', 'true').lower() == 'true',
            log_queries=os.getenv('LOG_QUERIES', 'true').lower() == 'true',
            performance_tracking=os.getenv('PERFORMANCE_TRACKING', 'true').lower() == 'true',
            error_reporting=os.getenv('ERROR_REPORTING', 'true').lower() == 'true',
            health_check_interval=int(os.getenv('HEALTH_CHECK_INTERVAL', 60))
        )
    
    def _validate_config(self):
        """Validate configuration settings"""
        errors = []
        
        # Validate API keys
        if not self.api.openai_api_key:
            errors.append("OPENAI_API_KEY is required")
        
        # Validate database config for non-SQLite
        if self.database.type != 'sqlite':
            if not self.database.host:
                errors.append("Database host is required for non-SQLite databases")
            if not self.database.username:
                errors.append("Database username is required for non-SQLite databases")
            if not self.database.password:
                errors.append("Database password is required for non-SQLite databases")
        
        # Validate production settings
        if self.app.environment == Environment.PRODUCTION:
            if self.app.debug:
                errors.append("Debug mode should be disabled in production")
            if self.app.secret_key == 'dev-secret-key':
                errors.append("Production secret key should not use default value")
        
        if errors:
            for error in errors:
                self.logger.error(f"Configuration error: {error}")
            
            if self.app.environment == Environment.PRODUCTION:
                raise ValueError("Critical configuration errors in production environment")
            else:
                self.logger.warning("Configuration validation found issues (non-production)")
    
    def get_database_url(self) -> str:
        """Get database connection URL"""
        if self.database.type == 'sqlite':
            return f"sqlite:///{self.database.database}"
        elif self.database.type == 'postgresql':
            return (
                f"postgresql://{self.database.username}:{self.database.password}"
                f"@{self.database.host}:{self.database.port}/{self.database.database}"
                f"?sslmode={self.database.ssl_mode}"
            )
        elif self.database.type == 'mysql':
            return (
                f"mysql+pymysql://{self.database.username}:{self.database.password}"
                f"@{self.database.host}:{self.database.port}/{self.database.database}"
            )
        else:
            raise ValueError(f"Unsupported database type: {self.database.type}")
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.app.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.app.environment == Environment.DEVELOPMENT
    
    def export_config(self, file_path: str = None) -> Dict[str, Any]:
        """Export configuration to file or return as dict"""
        config_dict = {
            'database': asdict(self.database),
            'api': {k: v for k, v in asdict(self.api).items() if 'key' not in k.lower()},  # Hide API keys
            'app': asdict(self.app),
            'security': asdict(self.security),
            'monitoring': asdict(self.monitoring)
        }
        
        # Convert enum to string
        config_dict['app']['environment'] = self.app.environment.value
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(config_dict, f, indent=2)
                self.logger.info(f"Configuration exported to {file_path}")
            except Exception as e:
                self.logger.error(f"Failed to export configuration: {e}")
        
        return config_dict
    
    def get_health_check_config(self) -> Dict[str, Any]:
        """Get health check configuration"""
        return {
            'database_type': self.database.type,
            'environment': self.app.environment.value,
            'debug_mode': self.app.debug,
            'monitoring_enabled': self.monitoring.enable_metrics,
            'auth_enabled': self.security.enable_auth
        }
    
    def update_runtime_config(self, **kwargs):
        """Update configuration at runtime"""
        for key, value in kwargs.items():
            if hasattr(self.app, key):
                setattr(self.app, key, value)
                self.logger.info(f"Updated app config: {key} = {value}")
            elif hasattr(self.monitoring, key):
                setattr(self.monitoring, key, value)
                self.logger.info(f"Updated monitoring config: {key} = {value}")
            else:
                self.logger.warning(f"Unknown configuration key: {key}")

# Cloud deployment configurations
class CloudDeploymentConfigs:
    
    @staticmethod
    def aws_production() -> Dict[str, str]:
        """AWS production environment variables"""
        return {
            'ENVIRONMENT': 'production',
            'DEBUG': 'false',
            'LOG_LEVEL': 'INFO',
            'DB_TYPE': 'postgresql',
            'DB_SSL_MODE': 'require',
            'DB_POOL_SIZE': '20',
            'DB_MAX_OVERFLOW': '30',
            'ENABLE_METRICS': 'true',
            'RATE_LIMITING': 'true',
            'SESSION_TIMEOUT': '1800',
            'CORS_ORIGINS': 'https://yourdomain.com',
            'API_KEYS_ENABLED': 'true'
        }
    
    @staticmethod
    def digitalocean_production() -> Dict[str, str]:
        """DigitalOcean production environment variables"""
        return {
            'ENVIRONMENT': 'production',
            'DEBUG': 'false',
            'LOG_LEVEL': 'WARNING',
            'DB_TYPE': 'postgresql',
            'DB_SSL_MODE': 'require',
            'DB_POOL_SIZE': '15',
            'DB_MAX_OVERFLOW': '25',
            'ENABLE_METRICS': 'true',
            'RATE_LIMITING': 'true',
            'SESSION_TIMEOUT': '3600',
            'MAX_UPLOAD_SIZE': '100'
        }
    
    @staticmethod
    def local_development() -> Dict[str, str]:
        """Local development environment variables"""
        return {
            'ENVIRONMENT': 'development',
            'DEBUG': 'true',
            'LOG_LEVEL': 'DEBUG',
            'DB_TYPE': 'sqlite',
            'DB_NAME': 'data/development.db',
            'ENABLE_METRICS': 'true',
            'LOG_QUERIES': 'true',
            'PERFORMANCE_TRACKING': 'true',
            'RATE_LIMITING': 'false'
        }

def create_sample_env_file(env_type: str = "development"):
    """Create sample .env file for different environments"""
    
    if env_type == "development":
        env_content = """# Development Environment Configuration
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Database Configuration (SQLite for development)
DB_TYPE=sqlite
DB_NAME=data/development.db

# API Configuration
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Application Configuration
HOST=localhost
PORT=8501
SECRET_KEY=dev-secret-key-change-in-production

# Monitoring
ENABLE_METRICS=true
LOG_QUERIES=true
PERFORMANCE_TRACKING=true

# Security (relaxed for development)
ENABLE_AUTH=false
RATE_LIMITING=false
"""
    elif env_type == "production":
        env_content = """# Production Environment Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database Configuration (PostgreSQL for production)
DB_TYPE=postgresql
DB_HOST=your-db-host.com
DB_PORT=5432
DB_NAME=smart_sql_agent_prod
DB_USER=your_db_user
DB_PASSWORD=your_secure_db_password
DB_SSL_MODE=require
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# Alternative: Use DATABASE_URL for cloud deployments
# DATABASE_URL=postgresql://user:password@host:port/database

# API Configuration
OPENAI_API_KEY=your_production_openai_api_key
ANTHROPIC_API_KEY=your_production_anthropic_api_key
API_RATE_LIMIT=1000
API_TIMEOUT=60

# Application Configuration
HOST=0.0.0.0
PORT=8080
SECRET_KEY=your-super-secure-secret-key-here
MAX_UPLOAD_SIZE=200

# Security (strict for production)
ENABLE_AUTH=true
API_KEYS_ENABLED=true
RATE_LIMITING=true
SESSION_TIMEOUT=1800
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# Monitoring
ENABLE_METRICS=true
LOG_QUERIES=false
PERFORMANCE_TRACKING=true
ERROR_REPORTING=true
HEALTH_CHECK_INTERVAL=60
"""
    else:
        env_content = """# Staging Environment Configuration
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO

# Database Configuration
DB_TYPE=postgresql
DB_HOST=staging-db-host.com
DB_PORT=5432
DB_NAME=smart_sql_agent_staging
DB_USER=staging_user
DB_PASSWORD=staging_password
DB_SSL_MODE=require

# API Configuration
OPENAI_API_KEY=your_staging_openai_api_key
API_RATE_LIMIT=500

# Application Configuration
HOST=0.0.0.0
PORT=8501
SECRET_KEY=staging-secret-key

# Security (moderate for staging)
ENABLE_AUTH=false
RATE_LIMITING=true
"""
    
    filename = f".env.{env_type}"
    
    try:
        with open(filename, 'w') as f:
            f.write(env_content)
        print(f"✅ Created sample environment file: {filename}")
        print(f"📝 Please edit {filename} with your actual values")
        return filename
    except Exception as e:
        print(f"❌ Failed to create {filename}: {e}")
        return None

def test_config_manager():
    """Test configuration manager functionality"""
    print("🧪 Testing Configuration Manager...")
    
    try:
        # Test with default configuration
        config = ConfigManager()
        
        print(f"✅ Environment: {config.app.environment.value}")
        print(f"✅ Database Type: {config.database.type}")
        print(f"✅ Debug Mode: {config.app.debug}")
        print(f"✅ API Key Present: {'Yes' if config.api.openai_api_key else 'No'}")
        
        # Test database URL generation
        try:
            db_url = config.get_database_url()
            print(f"✅ Database URL: {db_url[:50]}...")
        except Exception as e:
            print(f"⚠️ Database URL: {e}")
        
        # Test configuration export
        config_dict = config.export_config()
        print(f"✅ Config Export: {len(config_dict)} sections")
        
        # Test health check config
        health_config = config.get_health_check_config()
        print(f"✅ Health Check Config: {health_config}")
        
        # Test runtime updates
        config.update_runtime_config(debug=False, log_level='WARNING')
        print(f"✅ Runtime Update: Debug={config.app.debug}")
        
        print("✅ Configuration Manager test completed successfully!")
        
        return config
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "create-env":
            env_type = sys.argv[2] if len(sys.argv) > 2 else "development"
            create_sample_env_file(env_type)
        else:
            print("Usage: python config_manager.py [create-env] [development|staging|production]")
    else:
        test_config_manager()