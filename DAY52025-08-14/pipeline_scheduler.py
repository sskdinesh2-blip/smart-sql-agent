# src/pipeline_scheduler.py
"""
Automated Pipeline Scheduling System
Enterprise-level pipeline scheduling with cron-like functionality and monitoring
"""

import schedule
import time
import threading
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import sqlite3
import pandas as pd

# Import our systems
from logging_manager import SmartSQLLogger
from enhanced_sql_agent import EnhancedSQLPipelineAgent
from cloud_database_manager import CloudDatabaseManager

class ScheduleStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    RUNNING = "running"

class ExecutionStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    RUNNING = "running"
    PENDING = "pending"

@dataclass
class ScheduledPipeline:
    """Represents a scheduled SQL pipeline"""
    id: str
    name: str
    description: str
    requirement: str
    schedule_expression: str  # e.g., "daily", "hourly", "weekly"
    schedule_time: str  # e.g., "09:00", "14:30"
    database_config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    status: ScheduleStatus
    last_execution: Optional[datetime] = None
    next_execution: Optional[datetime] = None
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    created_by: str = "system"

@dataclass
class ExecutionResult:
    """Represents the result of a pipeline execution"""
    execution_id: str
    pipeline_id: str
    execution_time: datetime
    status: ExecutionStatus
    duration_seconds: float
    rows_affected: int
    sql_generated: str
    error_message: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None

class PipelineScheduler:
    """
    Enterprise pipeline scheduling system with monitoring and error recovery
    """
    
    def __init__(self, db_path: str = "data/scheduler.db"):
        self.logger = SmartSQLLogger()
        self.sql_agent = EnhancedSQLPipelineAgent()
        self.db_manager = CloudDatabaseManager()
        self.db_path = db_path
        
        # Initialize database
        self._init_database()
        
        # Schedule management
        self.scheduled_pipelines: Dict[str, ScheduledPipeline] = {}
        self.execution_results: List[ExecutionResult] = []
        self.is_running = False
        self.scheduler_thread = None
        
        # Load existing schedules
        self._load_schedules()
        
        self.logger.log_user_activity("scheduler_initialized", "system", {
            "db_path": db_path,
            "loaded_schedules": len(self.scheduled_pipelines)
        })

    def _init_database(self):
        """Initialize SQLite database for storing schedules and results"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create schedules table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_pipelines (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    requirement TEXT NOT NULL,
                    schedule_expression TEXT NOT NULL,
                    schedule_time TEXT NOT NULL,
                    database_config TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    status TEXT NOT NULL,
                    last_execution TIMESTAMP,
                    next_execution TIMESTAMP,
                    execution_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    created_by TEXT DEFAULT 'system'
                )
            """)
            
            # Create execution results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS execution_results (
                    execution_id TEXT PRIMARY KEY,
                    pipeline_id TEXT NOT NULL,
                    execution_time TIMESTAMP NOT NULL,
                    status TEXT NOT NULL,
                    duration_seconds REAL NOT NULL,
                    rows_affected INTEGER DEFAULT 0,
                    sql_generated TEXT,
                    error_message TEXT,
                    performance_metrics TEXT,
                    FOREIGN KEY (pipeline_id) REFERENCES scheduled_pipelines (id)
                )
            """)
            
            conn.commit()
            conn.close()
            
            self.logger.log_user_activity("database_initialized", "system", {
                "db_path": self.db_path,
                "tables_created": ["scheduled_pipelines", "execution_results"]
            })
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "database_initialization"})
            raise

    def _load_schedules(self):
        """Load existing schedules from database"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT * FROM scheduled_pipelines", conn)
            conn.close()
            
            for _, row in df.iterrows():
                pipeline = ScheduledPipeline(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    requirement=row['requirement'],
                    schedule_expression=row['schedule_expression'],
                    schedule_time=row['schedule_time'],
                    database_config=json.loads(row['database_config']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']),
                    status=ScheduleStatus(row['status']),
                    last_execution=datetime.fromisoformat(row['last_execution']) if row['last_execution'] else None,
                    next_execution=datetime.fromisoformat(row['next_execution']) if row['next_execution'] else None,
                    execution_count=row['execution_count'],
                    success_count=row['success_count'],
                    failure_count=row['failure_count'],
                    created_by=row['created_by']
                )
                
                self.scheduled_pipelines[pipeline.id] = pipeline
                
        except Exception as e:
            # Database might be empty or not exist yet
            self.logger.log_user_activity("load_schedules_info", "system", {
                "message": "No existing schedules found or database empty",
                "error": str(e)
            })

    def create_schedule(self, name: str, description: str, requirement: str,
                       schedule_expression: str, schedule_time: str,
                       database_config: Dict[str, Any], created_by: str = "user") -> str:
        """Create a new scheduled pipeline"""
        
        pipeline_id = str(uuid.uuid4())
        current_time = datetime.now()
        
        # Calculate next execution time
        next_execution = self._calculate_next_execution(schedule_expression, schedule_time)
        
        pipeline = ScheduledPipeline(
            id=pipeline_id,
            name=name,
            description=description,
            requirement=requirement,
            schedule_expression=schedule_expression,
            schedule_time=schedule_time,
            database_config=database_config,
            created_at=current_time,
            updated_at=current_time,
            status=ScheduleStatus.ACTIVE,
            next_execution=next_execution,
            created_by=created_by
        )
        
        # Save to database
        self._save_pipeline(pipeline)
        
        # Add to memory
        self.scheduled_pipelines[pipeline_id] = pipeline
        
        # Register with schedule library
        self._register_schedule(pipeline)
        
        self.logger.log_user_activity("schedule_created", created_by, {
            "pipeline_id": pipeline_id,
            "name": name,
            "schedule_expression": schedule_expression,
            "schedule_time": schedule_time,
            "next_execution": next_execution.isoformat()
        })
        
        return pipeline_id

    def _calculate_next_execution(self, expression: str, time_str: str) -> datetime:
        """Calculate next execution time based on schedule expression"""
        
        now = datetime.now()
        hour, minute = map(int, time_str.split(':'))
        
        if expression == "daily":
            next_exec = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_exec <= now:
                next_exec += timedelta(days=1)
        
        elif expression == "hourly":
            next_exec = now.replace(minute=minute, second=0, microsecond=0)
            if next_exec <= now:
                next_exec += timedelta(hours=1)
        
        elif expression == "weekly":
            # Weekly on current day of week
            next_exec = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_exec <= now:
                next_exec += timedelta(weeks=1)
        
        else:
            # Default to daily
            next_exec = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_exec <= now:
                next_exec += timedelta(days=1)
        
        return next_exec

    def _register_schedule(self, pipeline: ScheduledPipeline):
        """Register pipeline with schedule library"""
        
        def job_function():
            self._execute_pipeline(pipeline.id)
        
        if pipeline.schedule_expression == "daily":
            schedule.every().day.at(pipeline.schedule_time).do(job_function).tag(pipeline.id)
        elif pipeline.schedule_expression == "hourly":
            minute = int(pipeline.schedule_time.split(':')[1])
            schedule.every().hour.at(f":{minute:02d}").do(job_function).tag(pipeline.id)
        elif pipeline.schedule_expression == "weekly":
            schedule.every().week.at(pipeline.schedule_time).do(job_function).tag(pipeline.id)

    def _save_pipeline(self, pipeline: ScheduledPipeline):
        """Save pipeline to database"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO scheduled_pipelines 
                (id, name, description, requirement, schedule_expression, schedule_time,
                 database_config, created_at, updated_at, status, last_execution,
                 next_execution, execution_count, success_count, failure_count, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pipeline.id, pipeline.name, pipeline.description, pipeline.requirement,
                pipeline.schedule_expression, pipeline.schedule_time,
                json.dumps(pipeline.database_config),
                pipeline.created_at.isoformat(), pipeline.updated_at.isoformat(),
                pipeline.status.value,
                pipeline.last_execution.isoformat() if pipeline.last_execution else None,
                pipeline.next_execution.isoformat() if pipeline.next_execution else None,
                pipeline.execution_count, pipeline.success_count, pipeline.failure_count,
                pipeline.created_by
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "save_pipeline", "pipeline_id": pipeline.id})
            raise

    def _execute_pipeline(self, pipeline_id: str):
        """Execute a scheduled pipeline"""
        
        if pipeline_id not in self.scheduled_pipelines:
            self.logger.log_error(Exception(f"Pipeline {pipeline_id} not found"), {
                "operation": "execute_pipeline",
                "pipeline_id": pipeline_id
            })
            return
        
        pipeline = self.scheduled_pipelines[pipeline_id]
        execution_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        self.logger.log_user_activity("pipeline_execution_started", "scheduler", {
            "pipeline_id": pipeline_id,
            "execution_id": execution_id,
            "pipeline_name": pipeline.name
        })
        
        try:
            # Update pipeline status
            pipeline.status = ScheduleStatus.RUNNING
            pipeline.execution_count += 1
            self._save_pipeline(pipeline)
            
            # Generate SQL using the enhanced agent
            result = self.sql_agent.generate_pipeline(
                requirement=pipeline.requirement,
                database_type=pipeline.database_config.get('type', 'sqlite')
            )
            
            if not result.get('success', False):
                raise Exception("SQL generation failed")
            
            # Execute SQL if database config is provided
            rows_affected = 0
            if pipeline.database_config:
                db_result = self.sql_agent.execute_query(
                    sql=result['sql'],
                    database_config=pipeline.database_config
                )
                rows_affected = db_result.get('row_count', 0)
            
            # Calculate execution time
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Create execution result
            execution_result = ExecutionResult(
                execution_id=execution_id,
                pipeline_id=pipeline_id,
                execution_time=start_time,
                status=ExecutionStatus.SUCCESS,
                duration_seconds=duration,
                rows_affected=rows_affected,
                sql_generated=result['sql'],
                performance_metrics={
                    'generation_time': result.get('generation_time', 0),
                    'complexity': result.get('complexity', 'unknown'),
                    'execution_time': duration
                }
            )
            
            # Update pipeline success stats
            pipeline.status = ScheduleStatus.ACTIVE
            pipeline.success_count += 1
            pipeline.last_execution = start_time
            pipeline.next_execution = self._calculate_next_execution(
                pipeline.schedule_expression, pipeline.schedule_time
            )
            
            self.logger.log_user_activity("pipeline_execution_success", "scheduler", {
                "pipeline_id": pipeline_id,
                "execution_id": execution_id,
                "duration_seconds": duration,
                "rows_affected": rows_affected
            })
            
        except Exception as e:
            # Handle execution failure
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            execution_result = ExecutionResult(
                execution_id=execution_id,
                pipeline_id=pipeline_id,
                execution_time=start_time,
                status=ExecutionStatus.FAILED,
                duration_seconds=duration,
                rows_affected=0,
                sql_generated="",
                error_message=str(e)
            )
            
            # Update pipeline failure stats
            pipeline.status = ScheduleStatus.ACTIVE  # Keep active for retry
            pipeline.failure_count += 1
            pipeline.last_execution = start_time
            pipeline.next_execution = self._calculate_next_execution(
                pipeline.schedule_expression, pipeline.schedule_time
            )
            
            self.logger.log_error(e, {
                "operation": "pipeline_execution",
                "pipeline_id": pipeline_id,
                "execution_id": execution_id
            })
        
        # Save results
        self._save_execution_result(execution_result)
        self._save_pipeline(pipeline)
        self.execution_results.append(execution_result)

    def _save_execution_result(self, result: ExecutionResult):
        """Save execution result to database"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO execution_results 
                (execution_id, pipeline_id, execution_time, status, duration_seconds,
                 rows_affected, sql_generated, error_message, performance_metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.execution_id, result.pipeline_id,
                result.execution_time.isoformat(), result.status.value,
                result.duration_seconds, result.rows_affected,
                result.sql_generated, result.error_message,
                json.dumps(result.performance_metrics) if result.performance_metrics else None
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "save_execution_result"})

    def start_scheduler(self):
        """Start the pipeline scheduler"""
        
        if self.is_running:
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.log_user_activity("scheduler_started", "system", {
            "active_pipelines": len([p for p in self.scheduled_pipelines.values() 
                                   if p.status == ScheduleStatus.ACTIVE])
        })

    def stop_scheduler(self):
        """Stop the pipeline scheduler"""
        
        self.is_running = False
        schedule.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=2.0)
        
        self.logger.log_user_activity("scheduler_stopped", "system", {})

    def _scheduler_loop(self):
        """Main scheduler loop"""
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                self.logger.log_error(e, {"operation": "scheduler_loop"})
                time.sleep(60)  # Wait longer on error

    def get_pipeline_status(self, pipeline_id: str) -> Dict[str, Any]:
        """Get detailed status of a pipeline"""
        
        if pipeline_id not in self.scheduled_pipelines:
            return {"error": "Pipeline not found"}
        
        pipeline = self.scheduled_pipelines[pipeline_id]
        
        # Get recent execution results
        recent_executions = [
            asdict(result) for result in self.execution_results
            if result.pipeline_id == pipeline_id
        ][-10:]  # Last 10 executions
        
        return {
            "pipeline": asdict(pipeline),
            "recent_executions": recent_executions,
            "success_rate": (pipeline.success_count / max(pipeline.execution_count, 1)) * 100,
            "avg_duration": self._calculate_avg_duration(pipeline_id),
            "next_execution_in": self._time_until_next_execution(pipeline)
        }

    def _calculate_avg_duration(self, pipeline_id: str) -> float:
        """Calculate average execution duration for a pipeline"""
        
        durations = [
            result.duration_seconds for result in self.execution_results
            if result.pipeline_id == pipeline_id and result.status == ExecutionStatus.SUCCESS
        ]
        
        return sum(durations) / len(durations) if durations else 0.0

    def _time_until_next_execution(self, pipeline: ScheduledPipeline) -> str:
        """Calculate time until next execution"""
        
        if not pipeline.next_execution:
            return "Not scheduled"
        
        time_diff = pipeline.next_execution - datetime.now()
        
        if time_diff.total_seconds() < 0:
            return "Overdue"
        
        days = time_diff.days
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for the scheduler dashboard"""
        
        active_pipelines = [p for p in self.scheduled_pipelines.values() 
                          if p.status == ScheduleStatus.ACTIVE]
        
        recent_executions = sorted(
            self.execution_results,
            key=lambda x: x.execution_time,
            reverse=True
        )[:20]
        
        # Calculate statistics
        total_executions = len(self.execution_results)
        successful_executions = len([r for r in self.execution_results 
                                   if r.status == ExecutionStatus.SUCCESS])
        
        success_rate = (successful_executions / max(total_executions, 1)) * 100
        
        return {
            "total_pipelines": len(self.scheduled_pipelines),
            "active_pipelines": len(active_pipelines),
            "total_executions": total_executions,
            "success_rate": success_rate,
            "recent_executions": [asdict(r) for r in recent_executions],
            "scheduler_status": "RUNNING" if self.is_running else "STOPPED",
            "next_executions": [
                {
                    "pipeline_name": p.name,
                    "next_execution": p.next_execution.isoformat() if p.next_execution else None,
                    "time_until": self._time_until_next_execution(p)
                }
                for p in active_pipelines
                if p.next_execution
            ]
        }

    def pause_pipeline(self, pipeline_id: str):
        """Pause a scheduled pipeline"""
        
        if pipeline_id in self.scheduled_pipelines:
            pipeline = self.scheduled_pipelines[pipeline_id]
            pipeline.status = ScheduleStatus.PAUSED
            pipeline.updated_at = datetime.now()
            self._save_pipeline(pipeline)
            
            # Remove from schedule
            schedule.clear(pipeline_id)
            
            self.logger.log_user_activity("pipeline_paused", "user", {
                "pipeline_id": pipeline_id,
                "pipeline_name": pipeline.name
            })

    def resume_pipeline(self, pipeline_id: str):
        """Resume a paused pipeline"""
        
        if pipeline_id in self.scheduled_pipelines:
            pipeline = self.scheduled_pipelines[pipeline_id]
            pipeline.status = ScheduleStatus.ACTIVE
            pipeline.updated_at = datetime.now()
            pipeline.next_execution = self._calculate_next_execution(
                pipeline.schedule_expression, pipeline.schedule_time
            )
            self._save_pipeline(pipeline)
            
            # Re-register with schedule
            self._register_schedule(pipeline)
            
            self.logger.log_user_activity("pipeline_resumed", "user", {
                "pipeline_id": pipeline_id,
                "pipeline_name": pipeline.name,
                "next_execution": pipeline.next_execution.isoformat()
            })

    def delete_pipeline(self, pipeline_id: str):
        """Delete a scheduled pipeline"""
        
        if pipeline_id in self.scheduled_pipelines:
            pipeline = self.scheduled_pipelines[pipeline_id]
            
            # Remove from schedule
            schedule.clear(pipeline_id)
            
            # Remove from memory
            del self.scheduled_pipelines[pipeline_id]
            
            # Remove from database
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM scheduled_pipelines WHERE id = ?", (pipeline_id,))
                conn.commit()
                conn.close()
            except Exception as e:
                self.logger.log_error(e, {"operation": "delete_pipeline"})
            
            self.logger.log_user_activity("pipeline_deleted", "user", {
                "pipeline_id": pipeline_id,
                "pipeline_name": pipeline.name
            })

# 🧪 Test the pipeline scheduler
def main():
    """Test the pipeline scheduling system"""
    
    print("🧪 Testing Pipeline Scheduler...")
    
    # Initialize scheduler
    scheduler = PipelineScheduler()
    
    # Create a test schedule
    pipeline_id = scheduler.create_schedule(
        name="Daily Sales Report",
        description="Generate daily sales summary with customer metrics",
        requirement="Create a daily sales report showing total revenue, order count, and top customers",
        schedule_expression="daily",
        schedule_time="09:00",
        database_config={
            "type": "sqlite",
            "database": ":memory:"
        },
        created_by="test_user"
    )
    
    print(f"✅ Created pipeline: {pipeline_id}")
    
    # Get pipeline status
    status = scheduler.get_pipeline_status(pipeline_id)
    print(f"✅ Pipeline status: {status['pipeline']['status']}")
    print(f"✅ Next execution: {status['next_execution_in']}")
    
    # Start scheduler
    scheduler.start_scheduler()
    print("✅ Scheduler started")
    
    # Get dashboard data
    dashboard = scheduler.get_dashboard_data()
    print(f"✅ Dashboard data:")
    print(f"   - Total pipelines: {dashboard['total_pipelines']}")
    print(f"   - Active pipelines: {dashboard['active_pipelines']}")
    print(f"   - Scheduler status: {dashboard['scheduler_status']}")
    
    # Stop scheduler for clean exit
    scheduler.stop_scheduler()
    print("✅ Scheduler stopped")
    
    print("✅ Pipeline Scheduler test completed!")

if __name__ == "__main__":
    main()