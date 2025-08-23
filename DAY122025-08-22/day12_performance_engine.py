# src/day12_performance_engine.py
"""
Day 12: Performance Optimization & Scalability Engine
Advanced caching, query optimization, and auto-scaling capabilities
"""

import time
import hashlib
import json
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import concurrent.futures
from collections import defaultdict, OrderedDict
import psutil
import pickle
import gzip

class CacheStrategy(Enum):
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    ADAPTIVE = "adaptive"

class OptimizationLevel(Enum):
    BASIC = "basic"
    AGGRESSIVE = "aggressive"
    ADAPTIVE = "adaptive"
    CUSTOM = "custom"

@dataclass
class PerformanceMetrics:
    query_id: str
    execution_time: float
    cache_hit: bool
    optimization_applied: bool
    resource_usage: Dict[str, float]
    timestamp: datetime
    user_id: Optional[int] = None

@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl_seconds: Optional[int] = None
    compressed: bool = False

class IntelligentCache:
    """Advanced caching system with multiple strategies"""
    
    def __init__(self, max_size: int = 1000, strategy: CacheStrategy = CacheStrategy.ADAPTIVE):
        self.max_size = max_size
        self.strategy = strategy
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'size': 0
        }
        self.lock = threading.RLock()
        
    def _generate_key(self, query: str, params: Dict = None) -> str:
        """Generate cache key for query and parameters"""
        cache_input = f"{query}:{json.dumps(params or {}, sort_keys=True)}"
        return hashlib.sha256(cache_input.encode()).hexdigest()[:32]
    
    def _should_compress(self, value: Any) -> bool:
        """Determine if value should be compressed"""
        try:
            serialized = pickle.dumps(value)
            return len(serialized) > 1024  # Compress if > 1KB
        except:
            return False
    
    def _serialize_value(self, value: Any) -> Tuple[bytes, bool]:
        """Serialize and optionally compress value"""
        serialized = pickle.dumps(value)
        
        if self._should_compress(value):
            compressed = gzip.compress(serialized)
            return compressed, True
        
        return serialized, False
    
    def _deserialize_value(self, data: bytes, compressed: bool) -> Any:
        """Deserialize and optionally decompress value"""
        if compressed:
            decompressed = gzip.decompress(data)
            return pickle.loads(decompressed)
        
        return pickle.loads(data)
    
    def get(self, query: str, params: Dict = None) -> Optional[Any]:
        """Get value from cache"""
        key = self._generate_key(query, params)
        
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                
                # Check TTL expiration
                if entry.ttl_seconds:
                    age = (datetime.now() - entry.created_at).total_seconds()
                    if age > entry.ttl_seconds:
                        del self.cache[key]
                        self.stats['misses'] += 1
                        return None
                
                # Update access statistics
                entry.last_accessed = datetime.now()
                entry.access_count += 1
                
                # Move to end for LRU
                if self.strategy == CacheStrategy.LRU:
                    self.cache.move_to_end(key)
                
                self.stats['hits'] += 1
                return self._deserialize_value(entry.value, entry.compressed)
            
            self.stats['misses'] += 1
            return None
    
    def put(self, query: str, value: Any, params: Dict = None, ttl_seconds: Optional[int] = None):
        """Put value into cache"""
        key = self._generate_key(query, params)
        serialized_value, compressed = self._serialize_value(value)
        
        with self.lock:
            # Remove existing entry if present
            if key in self.cache:
                del self.cache[key]
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=serialized_value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1,
                ttl_seconds=ttl_seconds,
                compressed=compressed
            )
            
            # Evict if necessary
            while len(self.cache) >= self.max_size:
                self._evict_entry()
            
            self.cache[key] = entry
            self.stats['size'] = len(self.cache)
    
    def _evict_entry(self):
        """Evict entry based on strategy"""
        if not self.cache:
            return
        
        if self.strategy == CacheStrategy.LRU:
            # Remove least recently used (first in OrderedDict)
            self.cache.popitem(last=False)
        
        elif self.strategy == CacheStrategy.LFU:
            # Remove least frequently used
            min_access = min(entry.access_count for entry in self.cache.values())
            for key, entry in list(self.cache.items()):
                if entry.access_count == min_access:
                    del self.cache[key]
                    break
        
        elif self.strategy == CacheStrategy.TTL:
            # Remove expired entries first, then oldest
            now = datetime.now()
            for key, entry in list(self.cache.items()):
                if entry.ttl_seconds:
                    age = (now - entry.created_at).total_seconds()
                    if age > entry.ttl_seconds:
                        del self.cache[key]
                        break
            else:
                # No expired entries, remove oldest
                self.cache.popitem(last=False)
        
        elif self.strategy == CacheStrategy.ADAPTIVE:
            # Hybrid approach: consider both recency and frequency
            scores = {}
            now = datetime.now()
            
            for key, entry in self.cache.items():
                recency_score = (now - entry.last_accessed).total_seconds()
                frequency_score = 1.0 / (entry.access_count + 1)
                scores[key] = recency_score + frequency_score
            
            # Remove entry with highest score (oldest + least frequent)
            worst_key = max(scores, key=scores.get)
            del self.cache[worst_key]
        
        self.stats['evictions'] += 1
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.stats = {'hits': 0, 'misses': 0, 'evictions': 0, 'size': 0}
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        with self.lock:
            hit_rate = self.stats['hits'] / (self.stats['hits'] + self.stats['misses']) if (self.stats['hits'] + self.stats['misses']) > 0 else 0
            return {
                **self.stats,
                'hit_rate': round(hit_rate * 100, 2),
                'strategy': self.strategy.value
            }

class QueryOptimizer:
    """Advanced SQL query optimization engine"""
    
    def __init__(self):
        self.optimization_rules = self._load_optimization_rules()
        self.performance_history = defaultdict(list)
        
    def _load_optimization_rules(self) -> List[Dict]:
        """Load query optimization rules"""
        return [
            {
                'name': 'add_index_hints',
                'pattern': r'WHERE\s+(\w+)\s*[=<>]',
                'optimization': self._suggest_index,
                'priority': 1,
                'performance_gain': 0.3
            },
            {
                'name': 'optimize_joins',
                'pattern': r'JOIN.*ON\s+(\w+\.\w+)\s*=\s*(\w+\.\w+)',
                'optimization': self._optimize_join_order,
                'priority': 2,
                'performance_gain': 0.25
            },
            {
                'name': 'limit_result_sets',
                'pattern': r'SELECT.*FROM.*(?!LIMIT)',
                'optimization': self._add_limit_clause,
                'priority': 3,
                'performance_gain': 0.2
            },
            {
                'name': 'select_specific_columns',
                'pattern': r'SELECT\s+\*\s+FROM',
                'optimization': self._suggest_specific_columns,
                'priority': 4,
                'performance_gain': 0.15
            },
            {
                'name': 'optimize_subqueries',
                'pattern': r'IN\s*\(\s*SELECT',
                'optimization': self._convert_subquery_to_join,
                'priority': 5,
                'performance_gain': 0.35
            }
        ]
    
    def optimize_query(self, query: str, optimization_level: OptimizationLevel = OptimizationLevel.ADAPTIVE) -> Dict:
        """Optimize SQL query based on rules and historical performance"""
        
        optimizations = []
        optimized_query = query
        total_gain = 0.0
        
        # Apply optimization rules based on level
        rules_to_apply = self._select_rules(optimization_level)
        
        for rule in rules_to_apply:
            import re
            if re.search(rule['pattern'], query, re.IGNORECASE):
                optimization_result = rule['optimization'](query, rule)
                if optimization_result['applied']:
                    optimizations.append({
                        'rule': rule['name'],
                        'description': optimization_result['description'],
                        'estimated_gain': rule['performance_gain'],
                        'confidence': optimization_result['confidence']
                    })
                    optimized_query = optimization_result['optimized_query']
                    total_gain += rule['performance_gain']
        
        # Estimate performance improvement
        estimated_speedup = 1.0 + min(total_gain, 0.8)  # Cap at 80% improvement
        
        return {
            'original_query': query,
            'optimized_query': optimized_query,
            'optimizations': optimizations,
            'estimated_speedup': round(estimated_speedup, 2),
            'optimization_level': optimization_level.value,
            'applied_rules': len(optimizations)
        }
    
    def _select_rules(self, level: OptimizationLevel) -> List[Dict]:
        """Select optimization rules based on level"""
        if level == OptimizationLevel.BASIC:
            return [rule for rule in self.optimization_rules if rule['priority'] <= 2]
        elif level == OptimizationLevel.AGGRESSIVE:
            return self.optimization_rules  # Apply all rules
        elif level == OptimizationLevel.ADAPTIVE:
            # Select rules based on historical performance
            return [rule for rule in self.optimization_rules if rule['priority'] <= 4]
        else:
            return self.optimization_rules
    
    def _suggest_index(self, query: str, rule: Dict) -> Dict:
        """Suggest index creation"""
        import re
        matches = re.findall(rule['pattern'], query, re.IGNORECASE)
        if matches:
            column = matches[0]
            return {
                'applied': True,
                'optimized_query': query + f"\n-- OPTIMIZATION: Consider creating index on {column}",
                'description': f"Add index on column '{column}' for WHERE clause optimization",
                'confidence': 0.8
            }
        return {'applied': False}
    
    def _optimize_join_order(self, query: str, rule: Dict) -> Dict:
        """Optimize JOIN order"""
        return {
            'applied': True,
            'optimized_query': query + "\n-- OPTIMIZATION: Consider reordering JOINs - smaller tables first",
            'description': "Optimize JOIN order by placing smaller tables first",
            'confidence': 0.7
        }
    
    def _add_limit_clause(self, query: str, rule: Dict) -> Dict:
        """Add LIMIT clause if missing"""
        if 'LIMIT' not in query.upper():
            return {
                'applied': True,
                'optimized_query': query + " LIMIT 1000",
                'description': "Add LIMIT clause to prevent accidentally large result sets",
                'confidence': 0.9
            }
        return {'applied': False}
    
    def _suggest_specific_columns(self, query: str, rule: Dict) -> Dict:
        """Suggest specific column selection"""
        return {
            'applied': True,
            'optimized_query': query.replace('SELECT *', 'SELECT id, name, created_at -- Specify needed columns'),
            'description': "Replace SELECT * with specific columns to reduce data transfer",
            'confidence': 0.6
        }
    
    def _convert_subquery_to_join(self, query: str, rule: Dict) -> Dict:
        """Convert IN subquery to JOIN"""
        return {
            'applied': True,
            'optimized_query': query + "\n-- OPTIMIZATION: Consider converting IN subquery to JOIN for better performance",
            'description': "Convert IN subquery to JOIN operation for improved performance",
            'confidence': 0.75
        }

class LoadBalancer:
    """Intelligent load balancing for database connections"""
    
    def __init__(self):
        self.connections = {}
        self.connection_stats = defaultdict(lambda: {
            'active_queries': 0,
            'total_queries': 0,
            'average_response_time': 0.0,
            'error_count': 0,
            'last_health_check': datetime.now()
        })
        
    def register_connection(self, connection_id: str, config: Dict):
        """Register a database connection"""
        self.connections[connection_id] = {
            'config': config,
            'active': True,
            'weight': config.get('weight', 1.0),
            'max_connections': config.get('max_connections', 100)
        }
    
    def select_connection(self, query_type: str = 'read') -> Optional[str]:
        """Select optimal connection for query"""
        active_connections = {
            conn_id: conn for conn_id, conn in self.connections.items() 
            if conn['active']
        }
        
        if not active_connections:
            return None
        
        # Simple weighted round-robin with health consideration
        best_connection = None
        best_score = float('inf')
        
        for conn_id, conn in active_connections.items():
            stats = self.connection_stats[conn_id]
            
            # Calculate load score (lower is better)
            load_factor = stats['active_queries'] / conn['max_connections']
            response_factor = stats['average_response_time'] / 1000.0  # Convert to seconds
            error_factor = stats['error_count'] / max(stats['total_queries'], 1)
            
            score = (load_factor * 0.4) + (response_factor * 0.4) + (error_factor * 0.2)
            score = score / conn['weight']  # Apply weight
            
            if score < best_score:
                best_score = score
                best_connection = conn_id
        
        return best_connection
    
    def report_query_start(self, connection_id: str):
        """Report query start for load tracking"""
        if connection_id in self.connection_stats:
            self.connection_stats[connection_id]['active_queries'] += 1
            self.connection_stats[connection_id]['total_queries'] += 1
    
    def report_query_end(self, connection_id: str, execution_time: float, success: bool):
        """Report query completion"""
        if connection_id in self.connection_stats:
            stats = self.connection_stats[connection_id]
            stats['active_queries'] = max(0, stats['active_queries'] - 1)
            
            # Update average response time
            current_avg = stats['average_response_time']
            total_queries = stats['total_queries']
            stats['average_response_time'] = ((current_avg * (total_queries - 1)) + execution_time) / total_queries
            
            if not success:
                stats['error_count'] += 1

class AutoScaler:
    """Automatic scaling based on system metrics"""
    
    def __init__(self):
        self.scaling_rules = {
            'cpu_threshold': 70.0,
            'memory_threshold': 80.0,
            'response_time_threshold': 2.0,  # seconds
            'queue_length_threshold': 100,
            'scale_up_cooldown': 300,  # 5 minutes
            'scale_down_cooldown': 600,  # 10 minutes
            'min_instances': 1,
            'max_instances': 10
        }
        self.last_scale_action = datetime.now() - timedelta(hours=1)
        self.current_instances = 1
        
    def check_scaling_needs(self, metrics: Dict) -> Dict:
        """Check if scaling action is needed"""
        now = datetime.now()
        
        # Check cooldown period
        time_since_last_scale = (now - self.last_scale_action).total_seconds()
        
        scale_up_reasons = []
        scale_down_reasons = []
        
        # Analyze metrics
        cpu_usage = metrics.get('cpu_percent', 0)
        memory_usage = metrics.get('memory_percent', 0)
        response_time = metrics.get('average_response_time', 0)
        queue_length = metrics.get('queue_length', 0)
        
        # Scale up conditions
        if cpu_usage > self.scaling_rules['cpu_threshold']:
            scale_up_reasons.append(f"CPU usage {cpu_usage:.1f}% > {self.scaling_rules['cpu_threshold']}%")
        
        if memory_usage > self.scaling_rules['memory_threshold']:
            scale_up_reasons.append(f"Memory usage {memory_usage:.1f}% > {self.scaling_rules['memory_threshold']}%")
        
        if response_time > self.scaling_rules['response_time_threshold']:
            scale_up_reasons.append(f"Response time {response_time:.1f}s > {self.scaling_rules['response_time_threshold']}s")
        
        if queue_length > self.scaling_rules['queue_length_threshold']:
            scale_up_reasons.append(f"Queue length {queue_length} > {self.scaling_rules['queue_length_threshold']}")
        
        # Scale down conditions (all must be low)
        if (cpu_usage < self.scaling_rules['cpu_threshold'] * 0.5 and
            memory_usage < self.scaling_rules['memory_threshold'] * 0.5 and
            response_time < self.scaling_rules['response_time_threshold'] * 0.5):
            scale_down_reasons.append("All metrics are significantly below thresholds")
        
        # Determine action
        action = None
        
        if scale_up_reasons and time_since_last_scale >= self.scaling_rules['scale_up_cooldown']:
            if self.current_instances < self.scaling_rules['max_instances']:
                action = {
                    'type': 'scale_up',
                    'from_instances': self.current_instances,
                    'to_instances': min(self.current_instances + 1, self.scaling_rules['max_instances']),
                    'reasons': scale_up_reasons,
                    'cooldown_respected': True
                }
        
        elif scale_down_reasons and time_since_last_scale >= self.scaling_rules['scale_down_cooldown']:
            if self.current_instances > self.scaling_rules['min_instances']:
                action = {
                    'type': 'scale_down',
                    'from_instances': self.current_instances,
                    'to_instances': max(self.current_instances - 1, self.scaling_rules['min_instances']),
                    'reasons': scale_down_reasons,
                    'cooldown_respected': True
                }
        
        return {
            'action_needed': action is not None,
            'action': action,
            'current_instances': self.current_instances,
            'metrics_analyzed': metrics,
            'next_check_in': 60  # seconds
        }
    
    def execute_scaling_action(self, action: Dict) -> bool:
        """Execute scaling action"""
        if not action:
            return False
        
        try:
            # In a real implementation, this would trigger actual scaling
            # For now, just update our internal state
            
            old_instances = self.current_instances
            self.current_instances = action['to_instances']
            self.last_scale_action = datetime.now()
            
            print(f"Scaling action executed: {action['type']} from {old_instances} to {self.current_instances} instances")
            return True
            
        except Exception as e:
            print(f"Scaling action failed: {e}")
            return False

class PerformanceEngine:
    """Main performance optimization engine"""
    
    def __init__(self):
        self.cache = IntelligentCache(max_size=1000, strategy=CacheStrategy.ADAPTIVE)
        self.optimizer = QueryOptimizer()
        self.load_balancer = LoadBalancer()
        self.auto_scaler = AutoScaler()
        self.metrics_db = "data/performance_metrics.db"
        self.init_metrics_database()
        
    def init_metrics_database(self):
        """Initialize performance metrics database"""
        import os
        os.makedirs(os.path.dirname(self.metrics_db), exist_ok=True)
        
        conn = sqlite3.connect(self.metrics_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id TEXT NOT NULL,
                execution_time REAL NOT NULL,
                cache_hit BOOLEAN NOT NULL,
                optimization_applied BOOLEAN NOT NULL,
                resource_usage TEXT,
                timestamp TEXT NOT NULL,
                user_id INTEGER
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cpu_percent REAL,
                memory_percent REAL,
                disk_usage_percent REAL,
                active_connections INTEGER,
                queue_length INTEGER,
                average_response_time REAL,
                timestamp TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def execute_optimized_query(self, query: str, params: Dict = None, user_id: int = None) -> Dict:
        """Execute query with optimization and caching"""
        start_time = time.time()
        query_id = hashlib.sha256(f"{query}:{json.dumps(params or {})}".encode()).hexdigest()[:16]
        
        # Check cache first
        cached_result = self.cache.get(query, params)
        if cached_result is not None:
            execution_time = time.time() - start_time
            
            # Record metrics
            self._record_performance_metric(
                query_id, execution_time, True, False, user_id
            )
            
            return {
                'result': cached_result,
                'execution_time': execution_time,
                'cache_hit': True,
                'optimization_applied': False,
                'query_id': query_id
            }
        
        # Optimize query
        optimization_result = self.optimizer.optimize_query(query)
        optimized_query = optimization_result['optimized_query']
        optimization_applied = len(optimization_result['optimizations']) > 0
        
        # Select connection (simulate)
        connection_id = self.load_balancer.select_connection('read')
        
        # Execute query (simulate)
        execution_result = self._simulate_query_execution(optimized_query)
        execution_time = time.time() - start_time
        
        # Cache result
        cache_ttl = self._calculate_cache_ttl(query, execution_time)
        self.cache.put(query, execution_result, params, cache_ttl)
        
        # Record metrics
        self._record_performance_metric(
            query_id, execution_time, False, optimization_applied, user_id
        )
        
        return {
            'result': execution_result,
            'execution_time': execution_time,
            'cache_hit': False,
            'optimization_applied': optimization_applied,
            'optimization_details': optimization_result,
            'query_id': query_id
        }
    
    def _simulate_query_execution(self, query: str) -> Dict:
        """Simulate query execution"""
        # Simulate variable execution time based on query complexity
        base_time = 0.1
        complexity_factor = len(query) / 1000.0
        join_count = query.upper().count('JOIN') * 0.05
        
        simulated_time = base_time + complexity_factor + join_count
        time.sleep(min(simulated_time, 0.5))  # Cap simulation time
        
        return {
            'rows': 100 + int(complexity_factor * 1000),
            'columns': ['id', 'name', 'value', 'created_at'],
            'metadata': {
                'query_complexity': complexity_factor,
                'estimated_cost': simulated_time * 100
            }
        }
    
    def _calculate_cache_ttl(self, query: str, execution_time: float) -> int:
        """Calculate appropriate cache TTL based on query characteristics"""
        base_ttl = 300  # 5 minutes
        
        # Longer TTL for expensive queries
        if execution_time > 1.0:
            base_ttl *= 2
        
        # Shorter TTL for queries with current timestamp
        if 'NOW()' in query.upper() or 'CURRENT_TIMESTAMP' in query.upper():
            base_ttl = 60  # 1 minute
        
        # Longer TTL for analytical queries
        if any(keyword in query.upper() for keyword in ['GROUP BY', 'HAVING', 'WINDOW']):
            base_ttl *= 3
        
        return base_ttl
    
    def _record_performance_metric(self, query_id: str, execution_time: float, 
                                 cache_hit: bool, optimization_applied: bool, user_id: int = None):
        """Record performance metrics"""
        try:
            # Get current system metrics
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            
            resource_usage = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent
            }
            
            conn = sqlite3.connect(self.metrics_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO performance_metrics 
                (query_id, execution_time, cache_hit, optimization_applied, resource_usage, timestamp, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                query_id,
                execution_time,
                cache_hit,
                optimization_applied,
                json.dumps(resource_usage),
                datetime.now().isoformat(),
                user_id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error recording performance metric: {e}")
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary"""
        try:
            conn = sqlite3.connect(self.metrics_db)
            cursor = conn.cursor()
            
            # Get recent metrics
            cursor.execute("""
                SELECT 
                    AVG(execution_time) as avg_execution_time,
                    COUNT(*) as total_queries,
                    SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) as cache_hits,
                    SUM(CASE WHEN optimization_applied THEN 1 ELSE 0 END) as optimizations_applied
                FROM performance_metrics 
                WHERE timestamp > datetime('now', '-1 hour')
            """)
            
            row = cursor.fetchone()
            if row and row[1] > 0:  # If we have queries
                avg_execution_time, total_queries, cache_hits, optimizations_applied = row
                cache_hit_rate = (cache_hits / total_queries) * 100
                optimization_rate = (optimizations_applied / total_queries) * 100
            else:
                avg_execution_time = 0
                total_queries = 0
                cache_hit_rate = 0
                optimization_rate = 0
            
            conn.close()
            
            # Get cache stats
            cache_stats = self.cache.get_stats()
            
            # Get current system metrics
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            
            # Check if scaling is needed
            scaling_check = self.auto_scaler.check_scaling_needs({
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'average_response_time': avg_execution_time,
                'queue_length': 0  # Would be actual queue length in production
            })
            
            return {
                'performance_metrics': {
                    'average_execution_time': round(avg_execution_time, 3) if avg_execution_time else 0,
                    'total_queries_last_hour': total_queries,
                    'cache_hit_rate': round(cache_hit_rate, 1),
                    'optimization_rate': round(optimization_rate, 1)
                },
                'cache_statistics': cache_stats,
                'system_metrics': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory_percent,
                    'current_instances': self.auto_scaler.current_instances
                },
                'scaling_status': scaling_check,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'last_updated': datetime.now().isoformat()
            }

# Global performance engine instance
performance_engine = PerformanceEngine()

if __name__ == "__main__":
    # Test the performance engine
    engine = PerformanceEngine()
    
    print("Testing Performance Engine...")
    
    # Test query optimization
    test_query = "SELECT * FROM customers WHERE age > 25 AND city = 'New York'"
    
    print(f"\nOriginal Query: {test_query}")
    
    # Execute with optimization
    result1 = engine.execute_optimized_query(test_query)
    print(f"First execution - Time: {result1['execution_time']:.3f}s, Cache hit: {result1['cache_hit']}")
    
    # Execute same query again (should hit cache)
    result2 = engine.execute_optimized_query(test_query)
    print(f"Second execution - Time: {result2['execution_time']:.3f}s, Cache hit: {result2['cache_hit']}")
    
    # Test different query
    complex_query = """
    SELECT c.customer_name, COUNT(o.order_id) as order_count,
           SUM(o.total_amount) as total_spent
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    WHERE c.registration_date >= '2024-01-01'
    GROUP BY c.customer_id, c.customer_name
    HAVING COUNT(o.order_id) > 5
    ORDER BY total_spent DESC
    """
    
    result3 = engine.execute_optimized_query(complex_query)
    print(f"Complex query - Time: {result3['execution_time']:.3f}s, Optimizations: {result3['optimization_applied']}")
    
    if result3['optimization_applied']:
        print("Optimizations applied:")
        for opt in result3['optimization_details']['optimizations']:
            print(f"  - {opt['description']} (Est. gain: {opt['estimated_gain']*100:.1f}%)")
    
    # Get performance summary
    summary = engine.get_performance_summary()
    print(f"\nPerformance Summary:")
    print(f"Average execution time: {summary['performance_metrics']['average_execution_time']}s")
    print(f"Cache hit rate: {summary['cache_statistics']['hit_rate']}%")
    print(f"Current CPU usage: {summary['system_metrics']['cpu_percent']:.1f}%")
    
    scaling_status = summary['scaling_status']
    if scaling_status['action_needed']:
        action = scaling_status['action']
        print(f"Scaling recommendation: {action['type']} from {action['from_instances']} to {action['to_instances']} instances")
        print(f"Reasons: {', '.join(action['reasons'])}")
    else:
        print("No scaling action needed at this time")