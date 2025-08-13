# src/enhanced_sql_agent.py
import openai
import os
import time
import json
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from datetime import datetime

# Import our advanced systems
from logging_manager import SmartSQLLogger, track_performance, log_user_action
from error_recovery_manager import ErrorRecoveryManager, RecoveryStrategy
from cloud_database_manager import CloudDatabaseManager

load_dotenv()

class EnhancedSQLPipelineAgent:
    """
    Production-ready SQL Pipeline Agent with:
    - Advanced error recovery
    - Comprehensive logging
    - Performance monitoring
    - Cloud database integration
    - Smart fallback mechanisms
    """
    
    def __init__(self, user_id: Optional[str] = None):
        self.user_id = user_id or "anonymous"
        self.logger = SmartSQLLogger()
        self.recovery_manager = ErrorRecoveryManager()
        self.db_manager = CloudDatabaseManager()
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Setup recovery configurations
        self._setup_recovery_configurations()
        
        # Log agent initialization
        self.logger.log_user_activity("agent_initialized", self.user_id, {
            "timestamp": datetime.now().isoformat(),
            "features": ["error_recovery", "advanced_logging", "cloud_database"]
        })
    
    def _setup_recovery_configurations(self):
        """Setup error recovery configurations for all operations"""
        
        # SQL Generation recovery
        self.recovery_manager.register_retry_config(
            'sql_generation', 
            max_attempts=3, 
            base_delay=1.0, 
            max_delay=10.0
        )
        self.recovery_manager.register_fallback('sql_generation', self._sql_generation_fallback)
        self.recovery_manager.register_circuit_breaker('sql_generation', failure_threshold=5)
        
        # Database operations recovery
        self.recovery_manager.register_retry_config(
            'database_query', 
            max_attempts=2, 
            base_delay=0.5, 
            max_delay=5.0
        )
        self.recovery_manager.register_fallback('database_query', self._database_query_fallback)
        self.recovery_manager.register_circuit_breaker('database_query', failure_threshold=3)
        
        # Schema analysis recovery
        self.recovery_manager.register_retry_config(
            'schema_analysis', 
            max_attempts=2, 
            base_delay=0.5
        )
        self.recovery_manager.register_fallback('schema_analysis', self._schema_analysis_fallback)

    @track_performance("sql_pipeline_generation")
    @log_user_action("generate_pipeline")
    def generate_pipeline(self, requirement: str, schema_info: str = "", 
                         database_type: str = "postgresql") -> Dict[str, Any]:
        """Internal pipeline generation method"""
        
        # Use recovery manager for this operation
        return self.recovery_manager._execute_with_recovery(
            self._generate_pipeline_internal,
            'sql_generation',
            [RecoveryStrategy.RETRY, RecoveryStrategy.FALLBACK, RecoveryStrategy.GRACEFUL_DEGRADATION],
            requirement, schema_info, database_type
        )

    def _generate_pipeline_internal(self, requirement: str, schema_info: str = "", 
                                   database_type: str = "postgresql") -> Dict[str, Any]:
        
        start_time = time.time()
        
        try:
            # Validate inputs
            if not requirement.strip():
                raise ValueError("Requirement cannot be empty")
            
            # Log the generation request
            self.logger.log_user_activity("pipeline_generation_started", self.user_id, {
                "requirement_length": len(requirement),
                "has_schema": bool(schema_info.strip()),
                "database_type": database_type
            })
            
            # Generate SQL using OpenAI
            prompt = self._build_enhanced_prompt(requirement, schema_info, database_type)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{
                    "role": "system",
                    "content": "You are an expert SQL engineer. Generate production-ready SQL pipelines with comprehensive error handling, monitoring, and optimization."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.2,
                max_tokens=2000
            )
            
            sql_content = response.choices[0].message.content
            
            # Parse and enhance the generated SQL
            pipeline_result = self._parse_and_enhance_sql(sql_content, requirement, database_type)
            
            # Calculate metrics
            generation_time = time.time() - start_time
            
            # Log successful generation
            self.logger.log_performance("sql_generation", generation_time, {
                "requirement_complexity": self._analyze_requirement_complexity(requirement),
                "sql_lines": len(pipeline_result['sql'].split('\n')),
                "includes_monitoring": pipeline_result['includes_monitoring'],
                "database_type": database_type
            })
            
            # Log user activity
            self.logger.log_user_activity("pipeline_generated_successfully", self.user_id, {
                "generation_time": round(generation_time, 3),
                "sql_complexity": pipeline_result['complexity'],
                "validation_checks": len(pipeline_result['validation_checks']),
                "monitoring_metrics": len(pipeline_result['monitoring_metrics'])
            })
            
            return {
                "success": True,
                "sql": pipeline_result['sql'],
                "explanation": pipeline_result['explanation'],
                "complexity": pipeline_result['complexity'],
                "validation_checks": pipeline_result['validation_checks'],
                "monitoring_metrics": pipeline_result['monitoring_metrics'],
                "optimization_tips": pipeline_result['optimization_tips'],
                "estimated_performance": pipeline_result['estimated_performance'],
                "generation_time": round(generation_time, 3),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.log_error(e, {
                "operation": "generate_pipeline",
                "requirement": requirement[:100],
                "user_id": self.user_id,
                "generation_time": time.time() - start_time
            }, self.user_id)
            
            raise  # Let recovery manager handle this

    @track_performance("database_query_execution")
    @log_user_action("execute_query")
    def execute_query(self, sql: str, database_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute SQL query with advanced error handling and monitoring
        """
        
        return self.recovery_manager._execute_with_recovery(
            self._execute_query_internal,
            'database_query',
            [RecoveryStrategy.RETRY, RecoveryStrategy.FALLBACK],
            sql, database_config
        )

    def _execute_query_internal(self, sql: str, database_config: Dict[str, Any] = None):
        """Internal query execution method"""
        
        start_time = time.time()
        
        try:
            # Connect to database
            if database_config:
                success = self.db_manager.connect_to_database(
                    database_config['type'],
                    **database_config.get('config', {})
                )
                if not success:
                    raise ConnectionError("Failed to connect to database")
            
            # Execute query
            result = self.db_manager.execute_query(sql)
            execution_time = time.time() - start_time
            
            # Log query execution
            self.logger.log_sql_query(
                query=sql,
                execution_time=execution_time,
                rows_affected=len(result.get('rows', [])),
                database_type=self.db_manager.current_config.get('type', 'unknown'),
                user_id=self.user_id,
                success=True
            )
            
            return {
                "success": True,
                "rows": result.get('rows', []),
                "columns": result.get('columns', []),
                "execution_time": round(execution_time, 3),
                "row_count": len(result.get('rows', [])),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Log failed query
            self.logger.log_sql_query(
                query=sql,
                execution_time=execution_time,
                rows_affected=0,
                database_type=self.db_manager.current_config.get('type', 'unknown'),
                user_id=self.user_id,
                success=False
            )
            
            raise

    @track_performance("schema_analysis")
    @log_user_action("analyze_schema")
    def analyze_schema(self, database_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze database schema with error recovery
        """
        
        return self.recovery_manager._execute_with_recovery(
            self._analyze_schema_internal,
            'schema_analysis',
            [RecoveryStrategy.RETRY, RecoveryStrategy.FALLBACK],
            database_config
        )

    def _analyze_schema_internal(self, database_config: Dict[str, Any] = None):
        """Internal schema analysis method"""
        
        start_time = time.time()
        
        try:
            # Connect to database if config provided
            if database_config:
                success = self.db_manager.connect_to_database(
                    database_config['type'],
                    **database_config.get('config', {})
                )
                if not success:
                    raise ConnectionError("Failed to connect to database")
            
            # Get schema information
            schema_info = self.db_manager.get_schema_info()
            analysis_time = time.time() - start_time
            
            # Log schema analysis
            self.logger.log_performance("schema_analysis", analysis_time, {
                "table_count": len(schema_info.get('tables', [])),
                "database_type": self.db_manager.current_config.get('type', 'unknown'),
                "user_id": self.user_id
            })
            
            return {
                "success": True,
                "schema": schema_info,
                "analysis_time": round(analysis_time, 3),
                "table_count": len(schema_info.get('tables', [])),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.log_error(e, {
                "operation": "schema_analysis",
                "user_id": self.user_id
            }, self.user_id)
            
            raise

    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of the agent"""
        
        recovery_health = self.recovery_manager.get_health_report()
        db_health = self.db_manager.get_connection_status()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "HEALTHY" if recovery_health['overall_health'] == 'HEALTHY' and db_health['status'] else "DEGRADED",
            "components": {
                "error_recovery": recovery_health,
                "database": db_health,
                "openai_client": {"status": bool(self.client.api_key), "configured": True}
            },
            "user_id": self.user_id
        }

    def _build_enhanced_prompt(self, requirement: str, schema_info: str, database_type: str) -> str:
        """Build enhanced prompt for SQL generation"""
        
        return f"""
        Generate a comprehensive SQL data pipeline for the following requirement:
        
        **Requirement:** {requirement}
        
        **Database Type:** {database_type}
        
        **Schema Context:** {schema_info if schema_info else "No schema provided - use best practices"}
        
        **Please provide:**
        1. **Main SQL Query:** Production-ready SQL with proper CTEs, joins, and optimizations
        2. **Data Validation:** SQL checks for data quality and integrity
        3. **Performance Monitoring:** Metrics and monitoring queries
        4. **Error Handling:** SQL-level error handling and fallbacks
        5. **Optimization Tips:** Specific recommendations for performance
        6. **Execution Plan:** Step-by-step execution strategy
        
        **Requirements:**
        - Use proper indexing hints
        - Include comprehensive comments
        - Add execution time estimates
        - Provide fallback queries for critical paths
        - Include monitoring and alerting queries
        - Follow {database_type} best practices
        
        Format the response as structured sections with clear headings.
        """

    def _parse_and_enhance_sql(self, sql_content: str, requirement: str, database_type: str) -> Dict[str, Any]:
        """Parse and enhance generated SQL content"""
        
        # Basic parsing (in production, use more sophisticated parsing)
        lines = sql_content.split('\n')
        sql_lines = [line for line in lines if not line.strip().startswith('**') and line.strip()]
        
        complexity = self._analyze_sql_complexity(sql_content)
        
        return {
            "sql": '\n'.join(sql_lines),
            "explanation": f"Generated SQL pipeline for: {requirement}",
            "complexity": complexity,
            "validation_checks": self._extract_validation_checks(sql_content),
            "monitoring_metrics": self._extract_monitoring_metrics(sql_content),
            "optimization_tips": self._extract_optimization_tips(sql_content),
            "estimated_performance": self._estimate_performance(sql_content, complexity),
            "includes_monitoring": "monitoring" in sql_content.lower()
        }

    def _analyze_requirement_complexity(self, requirement: str) -> str:
        """Analyze requirement complexity"""
        
        complexity_indicators = {
            'simple': ['select', 'count', 'sum', 'basic'],
            'medium': ['join', 'group', 'aggregate', 'filter', 'order'],
            'complex': ['recursive', 'window', 'partition', 'advanced', 'optimization', 'performance']
        }
        
        requirement_lower = requirement.lower()
        
        for level, keywords in complexity_indicators.items():
            if any(keyword in requirement_lower for keyword in keywords):
                if level == 'complex':
                    return 'complex'
        
        return 'medium' if len(requirement.split()) > 10 else 'simple'

    def _analyze_sql_complexity(self, sql: str) -> str:
        """Analyze SQL complexity"""
        
        sql_lower = sql.lower()
        
        if any(keyword in sql_lower for keyword in ['recursive', 'window', 'partition']):
            return 'complex'
        elif any(keyword in sql_lower for keyword in ['join', 'group by', 'having']):
            return 'medium'
        else:
            return 'simple'

    def _extract_validation_checks(self, content: str) -> List[str]:
        """Extract validation checks from generated content"""
        
        # Basic extraction (enhance as needed)
        checks = []
        lines = content.lower().split('\n')
        
        for line in lines:
            if any(keyword in line for keyword in ['validation', 'check', 'constraint', 'verify']):
                checks.append(line.strip())
        
        return checks[:5]  # Return top 5 checks

    def _extract_monitoring_metrics(self, content: str) -> List[str]:
        """Extract monitoring metrics from generated content"""
        
        metrics = []
        lines = content.lower().split('\n')
        
        for line in lines:
            if any(keyword in line for keyword in ['monitor', 'metric', 'performance', 'track']):
                metrics.append(line.strip())
        
        return metrics[:5]  # Return top 5 metrics

    def _extract_optimization_tips(self, content: str) -> List[str]:
        """Extract optimization tips from generated content"""
        
        tips = []
        lines = content.lower().split('\n')
        
        for line in lines:
            if any(keyword in line for keyword in ['optimize', 'performance', 'index', 'efficient']):
                tips.append(line.strip())
        
        return tips[:5]  # Return top 5 tips

    def _estimate_performance(self, sql: str, complexity: str) -> Dict[str, Any]:
        """Estimate query performance"""
        
        base_times = {
            'simple': 0.05,
            'medium': 0.5,
            'complex': 2.0
        }
        
        estimated_time = base_times.get(complexity, 1.0)
        
        # Adjust based on SQL characteristics
        sql_lower = sql.lower()
        if 'join' in sql_lower:
            estimated_time *= 1.5
        if 'group by' in sql_lower:
            estimated_time *= 1.3
        if 'order by' in sql_lower:
            estimated_time *= 1.2
        
        return {
            "estimated_execution_time": round(estimated_time, 3),
            "complexity_factor": complexity,
            "optimization_potential": "high" if estimated_time > 1.0 else "low",
            "recommended_monitoring": estimated_time > 0.5
        }

    # Fallback methods for error recovery
    def _sql_generation_fallback(self, requirement: str, schema_info: str = "", database_type: str = "postgresql"):
        """Fallback SQL generation using simpler approach"""
        
        self.logger.log_user_activity("fallback_sql_generation", self.user_id, {
            "requirement": requirement[:100],
            "database_type": database_type,
            "reason": "Primary generation failed"
        })
        
        # Generate basic SQL based on requirement keywords
        requirement_lower = requirement.lower()
        
        if "report" in requirement_lower or "select" in requirement_lower:
            sql_template = self._generate_report_sql(requirement, schema_info, database_type)
        elif "update" in requirement_lower or "modify" in requirement_lower:
            sql_template = self._generate_update_sql(requirement, schema_info, database_type)
        elif "insert" in requirement_lower or "add" in requirement_lower:
            sql_template = self._generate_insert_sql(requirement, schema_info, database_type)
        else:
            sql_template = self._generate_default_sql(requirement, schema_info, database_type)
        
        return {
            "success": True,
            "sql": sql_template,
            "explanation": f"Fallback SQL generated for: {requirement}",
            "complexity": "simple",
            "validation_checks": ["-- Add appropriate WHERE clauses", "-- Verify column names exist"],
            "monitoring_metrics": ["-- Add execution time monitoring", "-- Add row count validation"],
            "optimization_tips": ["Review and optimize for your specific schema", "Add appropriate indexes"],
            "estimated_performance": {
                "estimated_execution_time": 0.1, 
                "complexity_factor": "simple",
                "optimization_potential": "medium",
                "recommended_monitoring": True
            },
            "includes_monitoring": False,
            "fallback": True,
            "generation_time": 0.01,
            "timestamp": datetime.now().isoformat()
        }

    def _generate_report_sql(self, requirement: str, schema_info: str, database_type: str) -> str:
        """Generate report-style SQL"""
        
        # Extract table names from schema if available
        tables = self._extract_table_names(schema_info)
        main_table = tables[0] if tables else "your_main_table"
        
        # Determine if this needs aggregation
        requirement_lower = requirement.lower()
        needs_grouping = any(word in requirement_lower for word in ['report', 'summary', 'total', 'count', 'segmentation', 'analysis'])
        
        if needs_grouping:
            return f"""-- Fallback Report SQL for: {requirement}
-- Database Type: {database_type}
-- Generated: {datetime.now().isoformat()}

SELECT 
    -- Main grouping columns (please customize)
    t1.id,
    t1.name,
    -- Aggregated metrics
    COUNT(*) as record_count,
    SUM(COALESCE(t1.amount, 0)) as total_amount,
    AVG(COALESCE(t1.amount, 0)) as avg_amount,
    CURRENT_TIMESTAMP as report_generated_at
FROM 
    {main_table} t1
WHERE 
    -- Add your filtering conditions
    1 = 1
    -- AND t1.active = true
    -- AND t1.created_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY 
    -- Group by non-aggregated columns
    t1.id, t1.name
HAVING
    -- Add having conditions if needed
    COUNT(*) > 0
ORDER BY 
    -- Add sorting criteria
    total_amount DESC, t1.id
LIMIT 1000;

-- Performance monitoring query
SELECT 
    'report_execution' as metric_name,
    COUNT(*) as total_rows,
    NOW() as execution_time
FROM {main_table};
"""
        else:
            return f"""-- Fallback Simple Report SQL for: {requirement}
-- Database Type: {database_type}
-- Generated: {datetime.now().isoformat()}

SELECT 
    -- Main columns (please customize)
    t1.*,
    CURRENT_TIMESTAMP as report_generated_at
FROM 
    {main_table} t1
WHERE 
    -- Add your filtering conditions
    1 = 1
    -- AND t1.active = true
    -- AND t1.created_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY 
    -- Add sorting criteria
    t1.id DESC
LIMIT 1000;

-- Summary query with GROUP BY for analysis
SELECT 
    COUNT(*) as total_records,
    COUNT(DISTINCT t1.id) as unique_records,
    'summary_stats' as report_type
FROM {main_table} t1
GROUP BY 'summary_stats';
"""

    def _generate_update_sql(self, requirement: str, schema_info: str, database_type: str) -> str:
        """Generate update-style SQL"""
        
        tables = self._extract_table_names(schema_info)
        main_table = tables[0] if tables else "your_table"
        
        return f"""-- Fallback Update SQL for: {requirement}
-- Database Type: {database_type}
-- Generated: {datetime.now().isoformat()}

-- Begin transaction for safety
BEGIN;

UPDATE {main_table}
SET 
    -- Specify columns to update
    updated_at = CURRENT_TIMESTAMP,
    modified_by = 'system'
    -- Add your update columns here
    -- column_name = new_value
WHERE 
    -- IMPORTANT: Add specific WHERE conditions
    -- Never run UPDATE without WHERE clause!
    id IN (
        SELECT id 
        FROM {main_table} 
        WHERE -- Add your selection criteria
        1 = 0  -- Replace with actual condition
    );

-- Verification query
SELECT 
    COUNT(*) as affected_rows,
    'update_verification' as operation
FROM {main_table}
WHERE updated_at >= CURRENT_TIMESTAMP - INTERVAL '1 minute';

-- Commit only after verification
-- COMMIT;
"""

    def _generate_insert_sql(self, requirement: str, schema_info: str, database_type: str) -> str:
        """Generate insert-style SQL"""
        
        tables = self._extract_table_names(schema_info)
        main_table = tables[0] if tables else "your_table"
        
        return f"""-- Fallback Insert SQL for: {requirement}
-- Database Type: {database_type}
-- Generated: {datetime.now().isoformat()}

INSERT INTO {main_table} (
    -- Specify column names
    id,
    created_at,
    updated_at
    -- Add your columns here
)
VALUES (
    -- Specify values
    DEFAULT,  -- for auto-increment id
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
    -- Add your values here
);

-- Or use INSERT with SELECT for bulk operations
INSERT INTO {main_table} (
    -- columns
    created_at,
    updated_at
)
SELECT 
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM source_table
WHERE -- Add conditions
    1 = 0;  -- Replace with actual condition

-- Verification
SELECT COUNT(*) as inserted_rows
FROM {main_table}
WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '1 minute';
"""

    def _generate_default_sql(self, requirement: str, schema_info: str, database_type: str) -> str:
        """Generate default SQL template"""
        
        return f"""-- Fallback SQL Template for: {requirement}
-- Database Type: {database_type}
-- Generated: {datetime.now().isoformat()}

-- This is a template based on your requirement
-- Please customize according to your needs

SELECT 
    -- Select appropriate columns
    *
FROM 
    -- Specify your table name
    your_table_name
WHERE 
    -- Add filtering conditions
    1 = 1
    -- Example conditions:
    -- AND status = 'active'
    -- AND created_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY 
    -- Add sorting
    id DESC
LIMIT 100;

-- Additional queries based on requirement analysis:
{self._generate_requirement_specific_queries(requirement)}

-- Monitoring and validation queries:
SELECT 
    COUNT(*) as total_records,
    MIN(created_date) as earliest_record,
    MAX(created_date) as latest_record,
    CURRENT_TIMESTAMP as analysis_time
FROM your_table_name;
"""

    def _generate_requirement_specific_queries(self, requirement: str) -> str:
        """Generate additional queries based on requirement keywords"""
        
        requirement_lower = requirement.lower()
        additional_queries = []
        
        if "daily" in requirement_lower:
            additional_queries.append("""
-- Daily aggregation query
SELECT 
    DATE(created_date) as day,
    COUNT(*) as daily_count
FROM your_table_name
WHERE created_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_date)
ORDER BY day DESC;""")
        
        if "customer" in requirement_lower:
            additional_queries.append("""
-- Customer analysis query
SELECT 
    customer_id,
    COUNT(*) as transaction_count,
    SUM(amount) as total_amount
FROM your_table_name
GROUP BY customer_id
ORDER BY total_amount DESC;""")
        
        if "trend" in requirement_lower or "analysis" in requirement_lower:
            additional_queries.append("""
-- Trend analysis query
SELECT 
    DATE_TRUNC('month', created_date) as month,
    COUNT(*) as monthly_count,
    AVG(amount) as avg_amount
FROM your_table_name
WHERE created_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', created_date)
ORDER BY month;""")
        
        return "\n".join(additional_queries) if additional_queries else "-- No additional queries generated"

    def _extract_table_names(self, schema_info: str) -> List[str]:
        """Extract table names from schema information"""
        
        if not schema_info:
            return []
        
        tables = []
        lines = schema_info.split('\n')
        
        for line in lines:
            line = line.strip()
            if '(' in line:  # Table definition like "users(id, name)"
                table_name = line.split('(')[0].strip()
                if table_name and not table_name.startswith('--'):
                    tables.append(table_name)
        
        return tables if tables else ["main_table"]

    def _database_query_fallback(self, sql: str, database_config: Dict[str, Any] = None):
        """Fallback for database query execution"""
        
        return {
            "success": False,
            "rows": [],
            "columns": [],
            "execution_time": 0,
            "row_count": 0,
            "error": "Database query failed - using fallback response",
            "fallback": True,
            "timestamp": datetime.now().isoformat()
        }

    def _schema_analysis_fallback(self, database_config: Dict[str, Any] = None):
        """Fallback for schema analysis"""
        
        return {
            "success": False,
            "schema": {"tables": [], "message": "Schema analysis unavailable"},
            "analysis_time": 0,
            "table_count": 0,
            "error": "Schema analysis failed - using fallback response",
            "fallback": True,
            "timestamp": datetime.now().isoformat()
        }

# 🧪 Test the enhanced SQL agent
if __name__ == "__main__":
    print("🧪 Testing Enhanced SQL Pipeline Agent...")
    
    # Initialize agent
    agent = EnhancedSQLPipelineAgent(user_id="test_user_123")
    
    # Test pipeline generation
    print("✅ Testing pipeline generation...")
    try:
        result = agent.generate_pipeline(
            requirement="Create a daily sales report with customer segmentation and trend analysis",
            schema_info="Tables: customers(id, name, segment), orders(id, customer_id, amount, date)",
            database_type="postgresql"
        )
        
        print(f"   Success: {result['success']}")
        print(f"   SQL Lines: {len(result['sql'].split())}")
        print(f"   Complexity: {result['complexity']}")
        print(f"   Generation Time: {result['generation_time']}s")
        
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test health status
    print("✅ Testing health status...")
    health = agent.get_health_status()
    print(f"   Overall Status: {health['overall_status']}")
    print(f"   Components: {list(health['components'].keys())}")
    
    print("✅ Enhanced SQL Pipeline Agent test completed!")
    print("🚀 Production features enabled:")
    print("   - Advanced error recovery with fallbacks")
    print("   - Comprehensive performance monitoring")
    print("   - Structured logging and analytics")
    print("   - Circuit breaker patterns")
    print("   - Health monitoring and reporting")