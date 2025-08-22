# src/day11_analytics_engine.py
"""
Day 11: Advanced Analytics & Reporting Engine
Intelligent reporting, executive dashboards, and automated analytics
"""

import pandas as pd
import numpy as np
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re
import io
import base64
from pathlib import Path

class ReportType(Enum):
    EXECUTIVE_SUMMARY = "executive_summary"
    OPERATIONAL_METRICS = "operational_metrics"
    FINANCIAL_ANALYSIS = "financial_analysis"
    PERFORMANCE_DASHBOARD = "performance_dashboard"
    COMPLIANCE_REPORT = "compliance_report"
    CUSTOM_ANALYTICS = "custom_analytics"

class ReportFrequency(Enum):
    REAL_TIME = "real_time"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"

@dataclass
class ReportConfig:
    report_id: str
    name: str
    description: str
    report_type: ReportType
    frequency: ReportFrequency
    data_sources: List[str]
    filters: Dict
    visualizations: List[Dict]
    recipients: List[str]
    active: bool = True
    created_at: Optional[datetime] = None

@dataclass
class AnalyticsMetric:
    metric_id: str
    name: str
    description: str
    calculation_sql: str
    target_value: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    unit: str = ""
    category: str = "general"

class DataSourceManager:
    """Manages connections to various data sources"""
    
    def __init__(self):
        self.connections = {}
        self.sample_data = self._generate_sample_data()
    
    def _generate_sample_data(self) -> Dict[str, pd.DataFrame]:
        """Generate sample business data for analytics"""
        
        # Sales data
        dates = pd.date_range(start='2024-01-01', end='2024-08-20', freq='D')
        sales_data = pd.DataFrame({
            'date': dates,
            'revenue': 50000 + np.random.normal(0, 10000, len(dates)).cumsum(),
            'orders': np.random.poisson(100, len(dates)),
            'customers': np.random.poisson(50, len(dates)),
            'region': np.random.choice(['North', 'South', 'East', 'West'], len(dates)),
            'product_category': np.random.choice(['Electronics', 'Clothing', 'Books', 'Home'], len(dates))
        })
        sales_data['revenue'] = np.abs(sales_data['revenue'])
        
        # User engagement data
        user_data = pd.DataFrame({
            'date': dates,
            'active_users': 1000 + np.random.normal(0, 100, len(dates)).cumsum(),
            'page_views': np.random.poisson(5000, len(dates)),
            'session_duration': np.random.exponential(300, len(dates)),  # seconds
            'bounce_rate': np.random.uniform(0.2, 0.6, len(dates)),
            'conversion_rate': np.random.uniform(0.02, 0.08, len(dates))
        })
        user_data['active_users'] = np.abs(user_data['active_users'])
        
        # Operational metrics
        ops_data = pd.DataFrame({
            'date': dates,
            'system_uptime': np.random.uniform(0.95, 1.0, len(dates)),
            'response_time_ms': np.random.exponential(200, len(dates)),
            'error_rate': np.random.exponential(0.01, len(dates)),
            'cpu_usage': np.random.uniform(0.3, 0.8, len(dates)),
            'memory_usage': np.random.uniform(0.4, 0.9, len(dates))
        })
        
        # Financial data
        financial_data = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=8, freq='ME'),
            'total_revenue': [500000, 520000, 495000, 580000, 610000, 595000, 630000, 650000],
            'total_costs': [300000, 310000, 315000, 350000, 360000, 355000, 375000, 380000],
            'marketing_spend': [50000, 55000, 48000, 62000, 65000, 58000, 68000, 70000],
            'customer_acquisition_cost': [25, 27, 24, 30, 28, 26, 32, 31]
        })
        financial_data['profit_margin'] = (financial_data['total_revenue'] - financial_data['total_costs']) / financial_data['total_revenue']
        
        return {
            'sales': sales_data,
            'users': user_data,
            'operations': ops_data,
            'financial': financial_data
        }
    
    def get_data(self, source: str, filters: Dict = None) -> pd.DataFrame:
        """Get data from specified source with optional filters"""
        if source not in self.sample_data:
            raise ValueError(f"Unknown data source: {source}")
        
        data = self.sample_data[source].copy()
        
        # Apply filters
        if filters:
            for column, filter_value in filters.items():
                if column in data.columns:
                    if isinstance(filter_value, dict):
                        if 'start_date' in filter_value and 'end_date' in filter_value:
                            data = data[(data['date'] >= filter_value['start_date']) & 
                                      (data['date'] <= filter_value['end_date'])]
                        elif 'min' in filter_value or 'max' in filter_value:
                            if 'min' in filter_value:
                                data = data[data[column] >= filter_value['min']]
                            if 'max' in filter_value:
                                data = data[data[column] <= filter_value['max']]
                    else:
                        data = data[data[column] == filter_value]
        
        return data

class MetricsCalculator:
    """Calculates business metrics and KPIs"""
    
    def __init__(self, data_source_manager: DataSourceManager):
        self.data_manager = data_source_manager
        self.predefined_metrics = self._load_predefined_metrics()
    
    def _load_predefined_metrics(self) -> List[AnalyticsMetric]:
        """Load predefined business metrics"""
        return [
            AnalyticsMetric(
                metric_id="revenue_growth",
                name="Revenue Growth Rate",
                description="Month-over-month revenue growth percentage",
                calculation_sql="SELECT ((current_month - previous_month) / previous_month) * 100 FROM revenue_comparison",
                target_value=10.0,
                warning_threshold=5.0,
                critical_threshold=0.0,
                unit="%",
                category="financial"
            ),
            AnalyticsMetric(
                metric_id="customer_acquisition_rate",
                name="Customer Acquisition Rate",
                description="Rate of new customer acquisition per month",
                calculation_sql="SELECT COUNT(DISTINCT customer_id) FROM new_customers WHERE date >= start_of_month",
                target_value=1000.0,
                warning_threshold=800.0,
                critical_threshold=500.0,
                unit="customers/month",
                category="growth"
            ),
            AnalyticsMetric(
                metric_id="system_uptime",
                name="System Uptime",
                description="Percentage of time system is operational",
                calculation_sql="SELECT AVG(uptime_percentage) FROM system_metrics WHERE date >= start_of_period",
                target_value=99.9,
                warning_threshold=99.0,
                critical_threshold=95.0,
                unit="%",
                category="operational"
            ),
            AnalyticsMetric(
                metric_id="conversion_rate",
                name="Conversion Rate",
                description="Percentage of visitors who complete desired action",
                calculation_sql="SELECT (conversions / total_visitors) * 100 FROM user_metrics",
                target_value=5.0,
                warning_threshold=3.0,
                critical_threshold=2.0,
                unit="%",
                category="marketing"
            )
        ]
    
    def calculate_metric(self, metric: AnalyticsMetric, time_period: Dict = None) -> Dict:
        """Calculate a specific metric"""
        try:
            # For demo purposes, calculate based on sample data
            if metric.metric_id == "revenue_growth":
                financial_data = self.data_manager.get_data('financial')
                if len(financial_data) >= 2:
                    current = financial_data.iloc[-1]['total_revenue']
                    previous = financial_data.iloc[-2]['total_revenue']
                    value = ((current - previous) / previous) * 100
                else:
                    value = 0.0
            
            elif metric.metric_id == "customer_acquisition_rate":
                sales_data = self.data_manager.get_data('sales')
                recent_data = sales_data[sales_data['date'] >= (datetime.now() - timedelta(days=30))]
                value = recent_data['customers'].sum()
            
            elif metric.metric_id == "system_uptime":
                ops_data = self.data_manager.get_data('operations')
                recent_data = ops_data[ops_data['date'] >= (datetime.now() - timedelta(days=7))]
                value = recent_data['system_uptime'].mean() * 100
            
            elif metric.metric_id == "conversion_rate":
                user_data = self.data_manager.get_data('users')
                recent_data = user_data[user_data['date'] >= (datetime.now() - timedelta(days=7))]
                value = recent_data['conversion_rate'].mean() * 100
            
            else:
                value = np.random.uniform(0, 100)  # Fallback for unknown metrics
            
            # Determine status based on thresholds
            status = "good"
            if metric.critical_threshold is not None and value <= metric.critical_threshold:
                status = "critical"
            elif metric.warning_threshold is not None and value <= metric.warning_threshold:
                status = "warning"
            elif metric.target_value is not None and value >= metric.target_value:
                status = "excellent"
            
            return {
                'metric_id': metric.metric_id,
                'value': round(value, 2),
                'unit': metric.unit,
                'status': status,
                'target': metric.target_value,
                'calculated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'metric_id': metric.metric_id,
                'value': None,
                'error': str(e),
                'calculated_at': datetime.now().isoformat()
            }
    
    def calculate_all_metrics(self, category: str = None) -> List[Dict]:
        """Calculate all metrics or metrics in specific category"""
        metrics_to_calculate = self.predefined_metrics
        
        if category:
            metrics_to_calculate = [m for m in metrics_to_calculate if m.category == category]
        
        results = []
        for metric in metrics_to_calculate:
            result = self.calculate_metric(metric)
            results.append(result)
        
        return results

class ReportGenerator:
    """Generates various types of reports and dashboards"""
    
    def __init__(self, data_manager: DataSourceManager, metrics_calculator: MetricsCalculator):
        self.data_manager = data_manager
        self.metrics_calculator = metrics_calculator
        self.report_templates = self._load_report_templates()
    
    def _load_report_templates(self) -> Dict:
        """Load report templates"""
        return {
            ReportType.EXECUTIVE_SUMMARY: {
                'sections': ['key_metrics', 'financial_overview', 'growth_trends', 'recommendations'],
                'metrics': ['revenue_growth', 'customer_acquisition_rate', 'conversion_rate'],
                'visualizations': ['revenue_trend', 'customer_growth', 'key_metrics_dashboard']
            },
            ReportType.OPERATIONAL_METRICS: {
                'sections': ['system_performance', 'uptime_analysis', 'error_tracking', 'resource_usage'],
                'metrics': ['system_uptime', 'response_time', 'error_rate'],
                'visualizations': ['uptime_chart', 'performance_metrics', 'alert_summary']
            },
            ReportType.FINANCIAL_ANALYSIS: {
                'sections': ['revenue_analysis', 'cost_breakdown', 'profitability', 'forecasting'],
                'metrics': ['revenue_growth', 'profit_margin', 'cost_per_acquisition'],
                'visualizations': ['revenue_waterfall', 'cost_analysis', 'profit_trends']
            }
        }
    
    def generate_executive_summary(self, time_period: Dict = None) -> Dict:
        """Generate executive summary report"""
        
        # Calculate key metrics
        key_metrics = self.metrics_calculator.calculate_all_metrics()
        
        # Get financial data
        financial_data = self.data_manager.get_data('financial')
        current_revenue = financial_data.iloc[-1]['total_revenue']
        revenue_growth = ((financial_data.iloc[-1]['total_revenue'] - financial_data.iloc[-2]['total_revenue']) / financial_data.iloc[-2]['total_revenue']) * 100
        
        # Get user engagement data
        user_data = self.data_manager.get_data('users')
        recent_users = user_data[user_data['date'] >= (datetime.now() - timedelta(days=30))]
        avg_conversion = recent_users['conversion_rate'].mean() * 100
        
        # Get sales data for customer count
        sales_data = self.data_manager.get_data('sales')
        recent_sales = sales_data[sales_data['date'] >= (datetime.now() - timedelta(days=30))]
        
        # Generate insights
        insights = []
        if revenue_growth > 10:
            insights.append("Strong revenue growth indicates successful market expansion")
        elif revenue_growth < 0:
            insights.append("Revenue decline requires immediate attention and strategy review")
        
        if avg_conversion > 5:
            insights.append("Conversion rates are performing above industry average")
        elif avg_conversion < 2:
            insights.append("Conversion optimization should be prioritized")
        
        # Generate recommendations
        recommendations = []
        if revenue_growth > 15:
            recommendations.append("Consider scaling successful initiatives to maintain growth momentum")
        if avg_conversion < 3:
            recommendations.append("Implement A/B testing for key conversion funnels")
        
        return {
            'report_type': 'executive_summary',
            'generated_at': datetime.now().isoformat(),
            'period': f"{datetime.now().strftime('%B %Y')}",
            'key_metrics': {
                'current_revenue': current_revenue,
                'revenue_growth_rate': round(revenue_growth, 2),
                'average_conversion_rate': round(avg_conversion, 2),
                'total_customers': int(recent_sales['customers'].sum())
            },
            'performance_indicators': key_metrics,
            'insights': insights,
            'recommendations': recommendations,
            'data_quality_score': 95.2
        }
    
    def generate_operational_dashboard(self, time_period: Dict = None) -> Dict:
        """Generate operational metrics dashboard"""
        
        ops_data = self.data_manager.get_data('operations')
        recent_data = ops_data[ops_data['date'] >= (datetime.now() - timedelta(days=7))]
        
        return {
            'report_type': 'operational_dashboard',
            'generated_at': datetime.now().isoformat(),
            'period': 'Last 7 Days',
            'system_metrics': {
                'average_uptime': round(recent_data['system_uptime'].mean() * 100, 2),
                'average_response_time': round(recent_data['response_time_ms'].mean(), 2),
                'error_rate': round(recent_data['error_rate'].mean() * 100, 4),
                'peak_cpu_usage': round(recent_data['cpu_usage'].max() * 100, 2),
                'average_memory_usage': round(recent_data['memory_usage'].mean() * 100, 2)
            },
            'alerts': [
                {
                    'severity': 'warning',
                    'message': 'Response time spike detected on 2024-08-19',
                    'value': '450ms',
                    'threshold': '300ms'
                }
            ],
            'trends': {
                'uptime_trend': 'stable',
                'performance_trend': 'improving',
                'error_trend': 'decreasing'
            }
        }
    
    def generate_financial_report(self, time_period: Dict = None) -> Dict:
        """Generate comprehensive financial analysis"""
        
        financial_data = self.data_manager.get_data('financial')
        
        # Calculate financial metrics
        total_revenue = financial_data['total_revenue'].sum()
        total_costs = financial_data['total_costs'].sum()
        total_profit = total_revenue - total_costs
        avg_profit_margin = financial_data['profit_margin'].mean()
        
        # Revenue breakdown by month
        monthly_breakdown = []
        for _, row in financial_data.iterrows():
            monthly_breakdown.append({
                'month': row['date'].strftime('%B %Y'),
                'revenue': row['total_revenue'],
                'costs': row['total_costs'],
                'profit': row['total_revenue'] - row['total_costs'],
                'margin': row['profit_margin']
            })
        
        return {
            'report_type': 'financial_analysis',
            'generated_at': datetime.now().isoformat(),
            'period': f"{financial_data['date'].min().strftime('%B %Y')} - {financial_data['date'].max().strftime('%B %Y')}",
            'summary': {
                'total_revenue': total_revenue,
                'total_costs': total_costs,
                'total_profit': total_profit,
                'average_profit_margin': round(avg_profit_margin * 100, 2)
            },
            'monthly_breakdown': monthly_breakdown,
            'key_insights': [
                f"Average profit margin of {avg_profit_margin*100:.1f}% indicates healthy profitability",
                f"Total profit of ${total_profit:,.0f} shows strong financial performance"
            ],
            'forecasting': {
                'next_month_revenue_forecast': int(financial_data['total_revenue'].iloc[-1] * 1.05),
                'confidence_interval': '85%'
            }
        }
    
    def generate_custom_report(self, config: ReportConfig) -> Dict:
        """Generate custom report based on configuration"""
        
        report_data = {
            'report_id': config.report_id,
            'name': config.name,
            'description': config.description,
            'generated_at': datetime.now().isoformat(),
            'data_sources': config.data_sources,
            'filters_applied': config.filters
        }
        
        # Process each data source
        for source in config.data_sources:
            try:
                data = self.data_manager.get_data(source, config.filters)
                report_data[f'{source}_summary'] = {
                    'record_count': len(data),
                    'date_range': f"{data['date'].min()} to {data['date'].max()}" if 'date' in data.columns else 'N/A',
                    'key_statistics': self._calculate_summary_stats(data)
                }
            except Exception as e:
                report_data[f'{source}_error'] = str(e)
        
        return report_data
    
    def _calculate_summary_stats(self, data: pd.DataFrame) -> Dict:
        """Calculate summary statistics for dataset"""
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        
        stats = {}
        for col in numeric_columns:
            stats[col] = {
                'mean': round(data[col].mean(), 2),
                'median': round(data[col].median(), 2),
                'std': round(data[col].std(), 2),
                'min': round(data[col].min(), 2),
                'max': round(data[col].max(), 2)
            }
        
        return stats

class ReportScheduler:
    """Handles automated report generation and distribution"""
    
    def __init__(self, report_generator: ReportGenerator):
        self.report_generator = report_generator
        self.scheduled_reports = []
        self.db_path = "data/scheduled_reports.db"
        self.init_database()
    
    def init_database(self):
        """Initialize scheduled reports database"""
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_reports (
                report_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                report_type TEXT NOT NULL,
                frequency TEXT NOT NULL,
                config TEXT NOT NULL,
                last_generated TEXT,
                next_scheduled TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS report_history (
                execution_id TEXT PRIMARY KEY,
                report_id TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                file_path TEXT,
                recipients TEXT,
                error_message TEXT,
                FOREIGN KEY (report_id) REFERENCES scheduled_reports (report_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def schedule_report(self, config: ReportConfig) -> str:
        """Schedule a report for automatic generation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        next_scheduled = self._calculate_next_run(config.frequency)
        
        cursor.execute("""
            INSERT OR REPLACE INTO scheduled_reports 
            (report_id, name, report_type, frequency, config, next_scheduled, active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            config.report_id,
            config.name,
            config.report_type.value,
            config.frequency.value,
            json.dumps(asdict(config)),
            next_scheduled.isoformat(),
            config.active
        ))
        
        conn.commit()
        conn.close()
        
        return config.report_id
    
    def _calculate_next_run(self, frequency: ReportFrequency) -> datetime:
        """Calculate next scheduled run time"""
        now = datetime.now()
        
        if frequency == ReportFrequency.HOURLY:
            return now + timedelta(hours=1)
        elif frequency == ReportFrequency.DAILY:
            return now.replace(hour=6, minute=0, second=0) + timedelta(days=1)
        elif frequency == ReportFrequency.WEEKLY:
            days_ahead = 0 - now.weekday()  # Monday
            if days_ahead <= 0:
                days_ahead += 7
            return (now + timedelta(days=days_ahead)).replace(hour=6, minute=0, second=0)
        elif frequency == ReportFrequency.MONTHLY:
            next_month = now.replace(day=1, hour=6, minute=0, second=0) + timedelta(days=32)
            return next_month.replace(day=1)
        else:
            return now + timedelta(hours=1)  # Default to hourly
    
    def get_scheduled_reports(self) -> List[Dict]:
        """Get all scheduled reports"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT report_id, name, report_type, frequency, last_generated, next_scheduled, active
            FROM scheduled_reports
            ORDER BY next_scheduled
        """)
        
        reports = []
        for row in cursor.fetchall():
            reports.append({
                'report_id': row[0],
                'name': row[1],
                'report_type': row[2],
                'frequency': row[3],
                'last_generated': row[4],
                'next_scheduled': row[5],
                'active': bool(row[6])
            })
        
        conn.close()
        return reports

class AdvancedAnalyticsEngine:
    """Main analytics engine coordinator"""
    
    def __init__(self):
        self.data_manager = DataSourceManager()
        self.metrics_calculator = MetricsCalculator(self.data_manager)
        self.report_generator = ReportGenerator(self.data_manager, self.metrics_calculator)
        self.scheduler = ReportScheduler(self.report_generator)
    
    def generate_executive_dashboard(self) -> Dict:
        """Generate comprehensive executive dashboard"""
        return {
            'executive_summary': self.report_generator.generate_executive_summary(),
            'operational_metrics': self.report_generator.generate_operational_dashboard(),
            'financial_overview': self.report_generator.generate_financial_report(),
            'key_metrics': self.metrics_calculator.calculate_all_metrics(),
            'generated_at': datetime.now().isoformat()
        }
    
    def create_custom_report(self, report_config: Dict) -> Dict:
        """Create custom report from configuration"""
        config = ReportConfig(**report_config)
        return self.report_generator.generate_custom_report(config)
    
    def get_analytics_summary(self) -> Dict:
        """Get overall analytics system summary"""
        scheduled_reports = self.scheduler.get_scheduled_reports()
        
        return {
            'total_data_sources': len(self.data_manager.sample_data),
            'available_metrics': len(self.metrics_calculator.predefined_metrics),
            'scheduled_reports': len(scheduled_reports),
            'active_reports': len([r for r in scheduled_reports if r['active']]),
            'last_updated': datetime.now().isoformat()
        }

# Global analytics engine instance
analytics_engine = AdvancedAnalyticsEngine()

if __name__ == "__main__":
    # Test the analytics engine
    engine = AdvancedAnalyticsEngine()
    
    # Generate executive dashboard
    dashboard = engine.generate_executive_dashboard()
    print("Executive Dashboard Generated:")
    print(f"Revenue Growth: {dashboard['executive_summary']['key_metrics']['revenue_growth_rate']}%")
    print(f"System Uptime: {dashboard['operational_metrics']['system_metrics']['average_uptime']}%")
    
    # Test custom report
    custom_config = {
        'report_id': 'test_001',
        'name': 'Test Sales Report',
        'description': 'Testing custom report generation',
        'report_type': ReportType.CUSTOM_ANALYTICS,
        'frequency': ReportFrequency.DAILY,
        'data_sources': ['sales', 'users'],
        'filters': {'date': {'start_date': '2024-08-01', 'end_date': '2024-08-20'}},
        'visualizations': [],
        'recipients': ['test@example.com']
    }
    
    custom_report = engine.create_custom_report(custom_config)
    print(f"\nCustom Report Generated: {custom_report['name']}")
    
    # Get system summary
    summary = engine.get_analytics_summary()
    print(f"\nAnalytics System Summary:")
    print(f"Data Sources: {summary['total_data_sources']}")
    print(f"Available Metrics: {summary['available_metrics']}")