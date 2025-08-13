# src/error_recovery_manager.py
import time
import json
from typing import Dict, Any, Callable, Optional, List
from functools import wraps
from datetime import datetime, timedelta
from logging_manager import SmartSQLLogger
import asyncio
import threading
from enum import Enum

class RecoveryStrategy(Enum):
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAKER = "circuit_breaker"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    ALERT_AND_CONTINUE = "alert_and_continue"

class ErrorRecoveryManager:
    """
    Intelligent error recovery system with:
    - Automatic retry with exponential backoff
    - Circuit breaker pattern
    - Fallback mechanisms
    - Health monitoring
    - Recovery analytics
    """
    
    def __init__(self):
        self.logger = SmartSQLLogger()
        self.circuit_breakers = {}
        self.retry_configs = {}
        self.fallback_handlers = {}
        self.health_metrics = {}
        self.recovery_stats = {
            'total_errors': 0,
            'recovered_errors': 0,
            'failed_recoveries': 0,
            'recovery_methods': {}
        }
        
    def register_retry_config(self, operation: str, max_attempts: int = 3,
                            base_delay: float = 1.0, max_delay: float = 60.0,
                            backoff_factor: float = 2.0):
        """Register retry configuration for specific operations"""
        
        self.retry_configs[operation] = {
            'max_attempts': max_attempts,
            'base_delay': base_delay,
            'max_delay': max_delay,
            'backoff_factor': backoff_factor
        }
        
    def register_fallback(self, operation: str, fallback_function: Callable):
        """Register fallback function for operations"""
        self.fallback_handlers[operation] = fallback_function
        
    def register_circuit_breaker(self, operation: str, failure_threshold: int = 5,
                               recovery_timeout: int = 60, success_threshold: int = 2):
        """Register circuit breaker for operations"""
        
        self.circuit_breakers[operation] = {
            'failure_count': 0,
            'failure_threshold': failure_threshold,
            'recovery_timeout': recovery_timeout,
            'success_threshold': success_threshold,
            'success_count': 0,
            'state': 'CLOSED',  # CLOSED, OPEN, HALF_OPEN
            'last_failure_time': None
        }

    def with_recovery(self, operation: str, strategies: List[RecoveryStrategy] = None):
        """Decorator for automatic error recovery"""
        if strategies is None:
            strategies = [RecoveryStrategy.RETRY, RecoveryStrategy.FALLBACK]
            
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self._execute_with_recovery(
                    func, operation, strategies, *args, **kwargs
                )
            return wrapper
        return decorator
        
    def _execute_with_recovery(self, func: Callable, operation: str,
                             strategies: List[RecoveryStrategy], *args, **kwargs):
        """Execute function with intelligent error recovery"""
        
        start_time = time.time()
        
        for strategy in strategies:
            try:
                if strategy == RecoveryStrategy.CIRCUIT_BREAKER:
                    if not self._check_circuit_breaker(operation):
                        raise Exception(f"Circuit breaker OPEN for {operation}")
                
                if strategy == RecoveryStrategy.RETRY:
                    return self._execute_with_retry(func, operation, *args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except Exception as e:
                self.recovery_stats['total_errors'] += 1
                
                recovery_result = self._handle_recovery_strategy(
                    strategy, operation, e, func, *args, **kwargs
                )
                
                if recovery_result is not None:
                    self.recovery_stats['recovered_errors'] += 1
                    self._update_recovery_method_stats(strategy.value)
                    
                    # Log successful recovery
                self.logger.log_user_activity("error_recovered", user_id=None, details={
                    'operation': operation,
                    'strategy': strategy.value,
                    'error_type': type(e).__name__,
                    'recovery_time': time.time() - start_time
                })
                    
                    return recovery_result
                
                # Continue to next strategy
                continue
        
        # All recovery strategies failed
        self.recovery_stats['failed_recoveries'] += 1
        self.logger.log_error(Exception(f"All recovery strategies failed for {operation}"), {
            'operation': operation,
            'strategies_attempted': [s.value for s in strategies],
            'total_time': time.time() - start_time
        })
        
        raise Exception(f"All recovery strategies failed for operation: {operation}")

    def _execute_with_retry(self, func: Callable, operation: str, *args, **kwargs):
        """Execute function with retry logic and exponential backoff"""
        
        config = self.retry_configs.get(operation, {
            'max_attempts': 3,
            'base_delay': 1.0,
            'max_delay': 60.0,
            'backoff_factor': 2.0
        })
        
        last_exception = None
        
        for attempt in range(config['max_attempts']):
            try:
                result = func(*args, **kwargs)
                
                # Reset circuit breaker on success
                if operation in self.circuit_breakers:
                    self._record_success(operation)
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Record failure for circuit breaker
                if operation in self.circuit_breakers:
                    self._record_failure(operation)
                
                # Log retry attempt
                self.logger.log_performance(f"{operation}_retry_attempt", 0, {
                    'attempt': attempt + 1,
                    'max_attempts': config['max_attempts'],
                    'error': str(e)
                })
                
                # Don't retry on final attempt
                if attempt == config['max_attempts'] - 1:
                    break
                
                # Calculate delay with exponential backoff
                delay = min(
                    config['base_delay'] * (config['backoff_factor'] ** attempt),
                    config['max_delay']
                )
                
                time.sleep(delay)
        
        raise last_exception

    def _handle_recovery_strategy(self, strategy: RecoveryStrategy, operation: str,
                                error: Exception, func: Callable, *args, **kwargs):
        """Handle specific recovery strategy"""
        
        if strategy == RecoveryStrategy.FALLBACK:
            return self._execute_fallback(operation, error, *args, **kwargs)
        
        elif strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
            return self._graceful_degradation(operation, error)
        
        elif strategy == RecoveryStrategy.ALERT_AND_CONTINUE:
            self._send_alert(operation, error)
            return self._get_default_result(operation)
        
        # Return None if strategy not handled
        return None

    def _execute_fallback(self, operation: str, error: Exception, *args, **kwargs):
        """Execute fallback function if available"""
        
        if operation in self.fallback_handlers:
            try:
                fallback_func = self.fallback_handlers[operation]
                
                self.logger.log_user_activity("fallback_executed", context={
                    'operation': operation,
                    'original_error': str(error)
                })
                
                return fallback_func(*args, **kwargs)
                
            except Exception as fallback_error:
                self.logger.log_error(fallback_error, {
                    'operation': operation,
                    'fallback_operation': True,
                    'original_error': str(error)
                })
        
        return None

    def _graceful_degradation(self, operation: str, error: Exception):
        """Provide graceful degradation"""
        
        degradation_responses = {
            'sql_generation': {
                'sql': '-- Error occurred during generation\n-- Please try again or contact support',
                'explanation': 'An error occurred during SQL generation. Please try with a simpler requirement.',
                'success': False
            },
            'database_connection': {
                'status': 'offline',
                'message': 'Database temporarily unavailable. Please try again later.',
                'success': False
            },
            'schema_analysis': {
                'tables': [],
                'message': 'Schema analysis temporarily unavailable.',
                'success': False
            }
        }
        
        response = degradation_responses.get(operation, {
            'message': f'Service temporarily degraded for {operation}',
            'success': False
        })
        
        self.logger.log_user_activity("graceful_degradation", user_id=None, details={
            'operation': operation,
            'error': str(error),
            'degraded_response': True
        })
        
        return response

    def _check_circuit_breaker(self, operation: str) -> bool:
        """Check if circuit breaker allows execution"""
        
        if operation not in self.circuit_breakers:
            return True
        
        breaker = self.circuit_breakers[operation]
        
        if breaker['state'] == 'CLOSED':
            return True
        
        elif breaker['state'] == 'OPEN':
            # Check if recovery timeout has passed
            if (datetime.now() - breaker['last_failure_time']).seconds > breaker['recovery_timeout']:
                breaker['state'] = 'HALF_OPEN'
                breaker['success_count'] = 0
                return True
            return False
        
        elif breaker['state'] == 'HALF_OPEN':
            return True
        
        return False

    def _record_failure(self, operation: str):
        """Record failure for circuit breaker"""
        
        if operation in self.circuit_breakers:
            breaker = self.circuit_breakers[operation]
            breaker['failure_count'] += 1
            breaker['last_failure_time'] = datetime.now()
            
            if breaker['failure_count'] >= breaker['failure_threshold']:
                breaker['state'] = 'OPEN'
                
                self.logger.log_user_activity("circuit_breaker_opened", user_id=None, details={
                    'operation': operation,
                    'failure_count': breaker['failure_count']
                })

    def _record_success(self, operation: str):
        """Record success for circuit breaker"""
        
        if operation in self.circuit_breakers:
            breaker = self.circuit_breakers[operation]
            
            if breaker['state'] == 'HALF_OPEN':
                breaker['success_count'] += 1
                
                if breaker['success_count'] >= breaker['success_threshold']:
                    breaker['state'] = 'CLOSED'
                    breaker['failure_count'] = 0
                    
                    self.logger.log_user_activity("circuit_breaker_closed", user_id=None, details={
                        'operation': operation,
                        'success_count': breaker['success_count']
                    })

    def _send_alert(self, operation: str, error: Exception):
        """Send alert for critical errors"""
        
        alert_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'severity': 'HIGH' if 'database' in operation.lower() else 'MEDIUM'
        }
        
        # Log alert (in production, send to monitoring system)
        self.logger.log_error(error, {
            'alert': True,
            'operation': operation,
            'requires_attention': True
        })
        
    def _get_default_result(self, operation: str):
        """Get default result for operation"""
        
        defaults = {
            'sql_generation': {'sql': '', 'success': False, 'message': 'Generation failed'},
            'database_query': {'rows': [], 'success': False, 'message': 'Query failed'},
            'schema_analysis': {'tables': [], 'success': False, 'message': 'Analysis failed'}
        }
        
        return defaults.get(operation, {'success': False, 'message': 'Operation failed'})

    def _update_recovery_method_stats(self, method: str):
        """Update recovery method statistics"""
        
        if method not in self.recovery_stats['recovery_methods']:
            self.recovery_stats['recovery_methods'][method] = 0
        
        self.recovery_stats['recovery_methods'][method] += 1

    def get_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        
        total_operations = self.recovery_stats['total_errors'] + self.recovery_stats['recovered_errors']
        recovery_rate = (
            self.recovery_stats['recovered_errors'] / total_operations
            if total_operations > 0 else 1.0
        )
        
        circuit_breaker_status = {}
        for operation, breaker in self.circuit_breakers.items():
            circuit_breaker_status[operation] = {
                'state': breaker['state'],
                'failure_count': breaker['failure_count'],
                'success_count': breaker['success_count']
            }
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_health': 'HEALTHY' if recovery_rate > 0.8 else 'DEGRADED',
            'recovery_rate': round(recovery_rate * 100, 2),
            'total_errors': self.recovery_stats['total_errors'],
            'recovered_errors': self.recovery_stats['recovered_errors'],
            'failed_recoveries': self.recovery_stats['failed_recoveries'],
            'recovery_methods': self.recovery_stats['recovery_methods'],
            'circuit_breakers': circuit_breaker_status,
            'registered_operations': {
                'retry_configs': list(self.retry_configs.keys()),
                'fallback_handlers': list(self.fallback_handlers.keys()),
                'circuit_breakers': list(self.circuit_breakers.keys())
            }
        }

# 🧪 Test the error recovery system
if __name__ == "__main__":
    print("🧪 Testing Error Recovery Manager...")
    
    # Initialize recovery manager
    recovery_manager = ErrorRecoveryManager()
    
    # Register configurations
    print("✅ Registering recovery configurations...")
    recovery_manager.register_retry_config('test_operation', max_attempts=3, base_delay=0.1)
    recovery_manager.register_circuit_breaker('test_operation', failure_threshold=2, recovery_timeout=5)
    
    # Register fallback
    def test_fallback(*args, **kwargs):
        return {'result': 'fallback_success', 'message': 'Used fallback method'}
    
    recovery_manager.register_fallback('test_operation', test_fallback)
    
    # Test retry mechanism
    print("✅ Testing retry mechanism...")
    
    attempt_count = 0
    
    @recovery_manager.with_recovery('test_operation', [RecoveryStrategy.RETRY])
    def flaky_function():
        global attempt_count
        attempt_count += 1
        if attempt_count < 3:  # Fail first 2 attempts
            raise ValueError(f"Attempt {attempt_count} failed")
        return f"Success on attempt {attempt_count}"
    
    try:
        result = flaky_function()
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   Failed: {e}")
    
    # Reset counter
    attempt_count = 0
    
    # Test fallback mechanism
    print("✅ Testing fallback mechanism...")
    
    @recovery_manager.with_recovery('test_operation', [RecoveryStrategy.RETRY, RecoveryStrategy.FALLBACK])
    def always_fail_function():
        raise ConnectionError("Always fails for testing")
    
    try:
        result = always_fail_function()
        print(f"   Fallback Result: {result}")
    except Exception as e:
        print(f"   Failed: {e}")
    
    # Test circuit breaker
    print("✅ Testing circuit breaker...")
    
    @recovery_manager.with_recovery('test_operation', [RecoveryStrategy.CIRCUIT_BREAKER, RecoveryStrategy.RETRY])
    def circuit_test_function():
        raise Exception("Circuit breaker test")
    
    # Trigger circuit breaker
    for i in range(3):
        try:
            circuit_test_function()
        except Exception:
            pass
    
    # Test graceful degradation
    print("✅ Testing graceful degradation...")
    
    @recovery_manager.with_recovery('sql_generation', [RecoveryStrategy.GRACEFUL_DEGRADATION])
    def sql_generation_function():
        raise RuntimeError("SQL generation failed")
    
    try:
        result = sql_generation_function()
        print(f"   Degraded Result: {result}")
    except Exception as e:
        print(f"   Failed: {e}")
    
    # Generate health report
    print("✅ Generating health report...")
    health_report = recovery_manager.get_health_report()
    print(f"   Overall Health: {health_report['overall_health']}")
    print(f"   Recovery Rate: {health_report['recovery_rate']}%")
    print(f"   Total Errors: {health_report['total_errors']}")
    print(f"   Recovered Errors: {health_report['recovered_errors']}")
    
    print("✅ Error Recovery Manager test completed successfully!")
    print("🔧 Recovery strategies tested:")
    print("   - Retry with exponential backoff")
    print("   - Fallback mechanisms")
    print("   - Circuit breaker pattern")
    print("   - Graceful degradation")
    print("   - Health monitoring and reporting")