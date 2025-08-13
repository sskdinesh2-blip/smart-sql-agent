# src/logging_manager.py
import logging
import json
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from functools import wraps
import sys

class SmartSQLLogger:
    """
    Advanced logging system for Smart SQL Agent with:
    - Structured JSON logging
    - Performance tracking
    - Error categorization
    - User activity monitoring
    - Production-ready formatting
    """
    
    def __init__(self, log_level: str = "INFO"):
        self.setup_logging(log_level)
        self.performance_metrics = {}
        
    def setup_logging(self, log_level: str):
        """Setup structured logging with multiple handlers"""
        
        # Create logs directory
        log_dir = Path("../logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure root logger
        logging.basicConfig(level=getattr(logging, log_level.upper()))
        
        # Create formatters
        json_formatter = JsonFormatter()
        console_formatter = ConsoleFormatter()
        
        # Create handlers
        self.setup_file_handlers(log_dir, json_formatter)
        self.setup_console_handler(console_formatter)
        
    def setup_file_handlers(self, log_dir: Path, formatter):
        """Setup file handlers for different log types"""
        
        handlers = {
            'app': log_dir / 'app.log',
            'sql': log_dir / 'sql_queries.log',
            'performance': log_dir / 'performance.log',
            'errors': log_dir / 'errors.log',
            'user_activity': log_dir / 'user_activity.log'
        }
        
        for handler_name, log_file in handlers.items():
            handler = logging.FileHandler(log_file)
            handler.setFormatter(formatter)
            
            logger = logging.getLogger(f'smart_sql.{handler_name}')
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            
    def setup_console_handler(self, formatter):
        """Setup console handler with colors"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        root_logger = logging.getLogger('smart_sql')
        root_logger.addHandler(console_handler)
        root_logger.setLevel(logging.INFO)

    def log_sql_query(self, query: str, execution_time: float, 
                     rows_affected: int, database_type: str,
                     user_id: Optional[str] = None, success: bool = True):
        """Log SQL query execution with detailed metrics"""
        
        logger = logging.getLogger('smart_sql.sql')
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'query_hash': str(abs(hash(query.strip())))[:8],
            'query_preview': query.strip()[:100] + '...' if len(query) > 100 else query.strip(),
            'execution_time_ms': round(execution_time * 1000, 3),
            'rows_affected': rows_affected,
            'database_type': database_type,
            'user_id': user_id,
            'success': success,
            'query_complexity': self._analyze_query_complexity(query)
        }
        
        if success:
            logger.info("SQL Query Executed", extra={'data': log_data})
        else:
            logger.error("SQL Query Failed", extra={'data': log_data})
            
    def log_performance(self, operation: str, duration: float, 
                       context: Dict[str, Any] = None):
        """Log performance metrics for operations"""
        
        logger = logging.getLogger('smart_sql.performance')
        
        # Store metrics for analysis
        if operation not in self.performance_metrics:
            self.performance_metrics[operation] = []
        
        self.performance_metrics[operation].append(duration)
        
        # Calculate statistics
        recent_times = self.performance_metrics[operation][-10:]  # Last 10 calls
        avg_time = sum(recent_times) / len(recent_times)
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'duration_ms': round(duration * 1000, 3),
            'avg_duration_ms': round(avg_time * 1000, 3),
            'context': context or {}
        }
        
        logger.info("Performance Metric", extra={'data': log_data})
        
    def log_user_activity(self, action: str, user_id: Optional[str] = None,
                         details: Dict[str, Any] = None):
        """Log user activities for analytics"""
        
        logger = logging.getLogger('smart_sql.user_activity')
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id or 'anonymous',
            'action': action,
            'details': details or {},
            'session_id': getattr(self, 'session_id', 'unknown')
        }
        
        logger.info("User Activity", extra={'data': log_data})
        
    def log_error(self, error: Exception, context: Dict[str, Any] = None,
                 user_id: Optional[str] = None):
        """Log errors with full context and stack traces"""
        
        logger = logging.getLogger('smart_sql.errors')
        
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'stack_trace': traceback.format_exc(),
            'context': context or {},
            'user_id': user_id,
            'severity': self._categorize_error(error)
        }
        
        logger.error("Application Error", extra={'data': log_data})
        
    def _analyze_query_complexity(self, query: str) -> str:
        """Analyze SQL query complexity"""
        query_lower = query.lower()
        
        complexity_indicators = {
            'simple': ['select', 'from', 'where'],
            'medium': ['join', 'group by', 'having', 'order by'],
            'complex': ['window', 'recursive', 'union', 'subquery', 'cte']
        }
        
        for level, keywords in complexity_indicators.items():
            if any(keyword in query_lower for keyword in keywords):
                if level == 'complex':
                    return 'complex'
        
        join_count = query_lower.count('join')
        if join_count > 2:
            return 'complex'
        elif join_count > 0:
            return 'medium'
        
        return 'simple'
        
    def _categorize_error(self, error: Exception) -> str:
        """Categorize error severity"""
        
        critical_errors = (ConnectionError, MemoryError, SystemError)
        high_errors = (ValueError, TypeError, AttributeError)
        medium_errors = (KeyError, IndexError, FileNotFoundError)
        
        if isinstance(error, critical_errors):
            return 'CRITICAL'
        elif isinstance(error, high_errors):
            return 'HIGH'
        elif isinstance(error, medium_errors):
            return 'MEDIUM'
        else:
            return 'LOW'

class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra data if present
        if hasattr(record, 'data'):
            log_entry.update(record.data)
            
        return json.dumps(log_entry, default=str)

class ConsoleFormatter(logging.Formatter):
    """Colored console formatter for development"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m'  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, '')
        reset = self.RESET
        
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        return f"{color}[{timestamp}] {record.levelname:<8} {record.name:<20} {record.getMessage()}{reset}"

def track_performance(operation_name: str = None):
    """Decorator to track function performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            operation = operation_name or f"{func.__module__}.{func.__name__}"
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log performance
                logger = SmartSQLLogger()
                logger.log_performance(operation, duration, {
                    'args_count': len(args),
                    'kwargs_count': len(kwargs),
                    'success': True
                })
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Log performance and error
                logger = SmartSQLLogger()
                logger.log_performance(operation, duration, {
                    'args_count': len(args),
                    'kwargs_count': len(kwargs),
                    'success': False,
                    'error': str(e)
                })
                logger.log_error(e, {'operation': operation})
                
                raise
                
        return wrapper
    return decorator

def log_user_action(action_name: str):
    """Decorator to log user actions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = SmartSQLLogger()
            
            # Extract user_id if present in kwargs
            user_id = kwargs.get('user_id', getattr(args[0], 'user_id', None) if args else None)
            
            # Log action start
            logger.log_user_activity(f"{action_name}_started", user_id, {
                'function': func.__name__,
                'args_count': len(args),
                'kwargs': list(kwargs.keys())
            })
            
            try:
                result = func(*args, **kwargs)
                
                # Log action success
                logger.log_user_activity(f"{action_name}_completed", user_id, {
                    'function': func.__name__,
                    'success': True
                })
                
                return result
                
            except Exception as e:
                # Log action failure
                logger.log_user_activity(f"{action_name}_failed", user_id, {
                    'function': func.__name__,
                    'error': str(e),
                    'success': False
                })
                
                raise
                
        return wrapper
    return decorator

# 🧪 Test the logging system
if __name__ == "__main__":
    print("🧪 Testing Advanced Logging System...")
    
    # Initialize logger
    logger = SmartSQLLogger(log_level="INFO")
    
    # Test SQL query logging
    print("✅ Testing SQL query logging...")
    logger.log_sql_query(
        query="SELECT * FROM users WHERE active = 1 ORDER BY created_at DESC",
        execution_time=0.045,
        rows_affected=150,
        database_type="postgresql",
        user_id="user123",
        success=True
    )
    
    # Test performance logging
    print("✅ Testing performance logging...")
    logger.log_performance("sql_generation", 1.234, {
        "input_length": 45,
        "output_lines": 12,
        "model": "gpt-4"
    })
    
    # Test user activity logging
    print("✅ Testing user activity logging...")
    logger.log_user_activity("pipeline_generated", "user123", {
        "requirement_length": 45,
        "schema_provided": True,
        "pipeline_complexity": "medium"
    })
    
    # Test error logging
    print("✅ Testing error logging...")
    try:
        raise ValueError("This is a test error for logging demonstration")
    except ValueError as e:
        logger.log_error(e, {
            "operation": "test_error_logging",
            "test_data": "sample"
        }, user_id="user123")
    
    # Test decorators
    print("✅ Testing decorators...")
    
    @track_performance("test_operation")
    @log_user_action("test_action")
    def test_function(duration=0.1):
        time.sleep(duration)
        return "success"
    
    result = test_function(0.05)
    
    print(f"✅ Advanced Logging System test completed successfully!")
    print("📁 Check the '../logs' directory for log files:")
    print("   - app.log (general application logs)")
    print("   - sql_queries.log (SQL execution logs)")
    print("   - performance.log (performance metrics)")
    print("   - errors.log (error tracking)")
    print("   - user_activity.log (user analytics)")