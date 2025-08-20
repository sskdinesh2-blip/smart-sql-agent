# src/day9_ml_integration.py
"""
Day 9: Machine Learning Integration & Predictive Analytics
AI-powered query optimization and intelligent insights
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, accuracy_score
import joblib
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re
import hashlib

@dataclass
class QueryPerformanceFeatures:
    """Features extracted from SQL queries for ML modeling"""
    query_length: int
    num_joins: int
    num_subqueries: int
    num_aggregations: int
    has_order_by: bool
    has_group_by: bool
    has_where_clause: bool
    estimated_table_size: int
    complexity_score: float

@dataclass
class QueryOptimizationSuggestion:
    """Query optimization suggestion"""
    original_query: str
    optimized_query: str
    improvement_type: str
    estimated_speedup: float
    confidence: float
    explanation: str

@dataclass
class BusinessInsight:
    """Generated business insight"""
    insight_type: str
    title: str
    description: str
    data_points: List[Dict]
    confidence: float
    actionable_recommendations: List[str]
    impact_level: str

class QueryAnalyzer:
    """Analyzes SQL queries to extract performance features"""
    
    def __init__(self):
        self.join_keywords = ['JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN']
        self.aggregation_functions = ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'GROUP_CONCAT']
    
    def extract_features(self, query: str, table_sizes: Dict[str, int] = None) -> QueryPerformanceFeatures:
        """Extract ML features from SQL query"""
        query_upper = query.upper()
        
        # Basic metrics
        query_length = len(query)
        
        # Count joins
        num_joins = sum(1 for keyword in self.join_keywords if keyword in query_upper)
        
        # Count subqueries
        num_subqueries = query_upper.count('(SELECT')
        
        # Count aggregations
        num_aggregations = sum(1 for func in self.aggregation_functions if func + '(' in query_upper)
        
        # Boolean features
        has_order_by = 'ORDER BY' in query_upper
        has_group_by = 'GROUP BY' in query_upper
        has_where_clause = 'WHERE' in query_upper
        
        # Estimate table size (simplified)
        estimated_table_size = self._estimate_table_size(query, table_sizes or {})
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(
            query_length, num_joins, num_subqueries, num_aggregations
        )
        
        return QueryPerformanceFeatures(
            query_length=query_length,
            num_joins=num_joins,
            num_subqueries=num_subqueries,
            num_aggregations=num_aggregations,
            has_order_by=has_order_by,
            has_group_by=has_group_by,
            has_where_clause=has_where_clause,
            estimated_table_size=estimated_table_size,
            complexity_score=complexity_score
        )
    
    def _estimate_table_size(self, query: str, table_sizes: Dict[str, int]) -> int:
        """Estimate total data size for query"""
        # Extract table names (simplified)
        tables = re.findall(r'FROM\s+(\w+)', query, re.IGNORECASE)
        tables.extend(re.findall(r'JOIN\s+(\w+)', query, re.IGNORECASE))
        
        total_size = 0
        for table in tables:
            total_size += table_sizes.get(table.lower(), 1000)  # Default size
        
        return total_size
    
    def _calculate_complexity_score(self, length: int, joins: int, subqueries: int, aggregations: int) -> float:
        """Calculate query complexity score"""
        # Weighted complexity formula
        score = (
            length * 0.001 +
            joins * 2.0 +
            subqueries * 3.0 +
            aggregations * 1.5
        )
        return min(score, 100.0)  # Cap at 100

class PerformancePredictionModel:
    """ML model for predicting query performance"""
    
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.analyzer = QueryAnalyzer()
    
    def prepare_training_data(self, query_history: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data from query execution history"""
        features = []
        targets = []
        
        for record in query_history:
            query_features = self.analyzer.extract_features(record['query'])
            
            # Convert features to array
            feature_array = [
                query_features.query_length,
                query_features.num_joins,
                query_features.num_subqueries,
                query_features.num_aggregations,
                int(query_features.has_order_by),
                int(query_features.has_group_by),
                int(query_features.has_where_clause),
                query_features.estimated_table_size,
                query_features.complexity_score
            ]
            
            features.append(feature_array)
            targets.append(record['execution_time'])
        
        return np.array(features), np.array(targets)
    
    def train(self, query_history: List[Dict]) -> Dict[str, float]:
        """Train the performance prediction model"""
        if len(query_history) < 10:
            # Generate synthetic training data for demo
            query_history = self._generate_synthetic_data()
        
        X, y = self.prepare_training_data(query_history)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_predictions = self.model.predict(X_train_scaled)
        test_predictions = self.model.predict(X_test_scaled)
        
        train_mse = mean_squared_error(y_train, train_predictions)
        test_mse = mean_squared_error(y_test, test_predictions)
        
        self.is_trained = True
        
        return {
            'train_mse': train_mse,
            'test_mse': test_mse,
            'train_samples': len(X_train),
            'test_samples': len(X_test)
        }
    
    def predict_performance(self, query: str) -> Dict[str, float]:
        """Predict query execution time and resource usage"""
        if not self.is_trained:
            return {'error': 'Model not trained'}
        
        features = self.analyzer.extract_features(query)
        feature_array = np.array([[
            features.query_length,
            features.num_joins,
            features.num_subqueries,
            features.num_aggregations,
            int(features.has_order_by),
            int(features.has_group_by),
            int(features.has_where_clause),
            features.estimated_table_size,
            features.complexity_score
        ]])
        
        feature_array_scaled = self.scaler.transform(feature_array)
        predicted_time = self.model.predict(feature_array_scaled)[0]
        
        # Get feature importance for explanation
        importance = self.model.feature_importances_
        feature_names = [
            'query_length', 'num_joins', 'num_subqueries', 'num_aggregations',
            'has_order_by', 'has_group_by', 'has_where_clause', 
            'estimated_table_size', 'complexity_score'
        ]
        
        return {
            'predicted_execution_time': max(0.1, predicted_time),
            'complexity_score': features.complexity_score,
            'performance_category': self._categorize_performance(predicted_time),
            'feature_importance': dict(zip(feature_names, importance))
        }
    
    def _categorize_performance(self, execution_time: float) -> str:
        """Categorize query performance"""
        if execution_time < 0.5:
            return 'fast'
        elif execution_time < 2.0:
            return 'moderate'
        elif execution_time < 5.0:
            return 'slow'
        else:
            return 'very_slow'
    
    def _generate_synthetic_data(self) -> List[Dict]:
        """Generate synthetic training data for demo"""
        synthetic_data = []
        
        queries = [
            "SELECT * FROM customers WHERE age > 25",
            "SELECT c.name, COUNT(o.id) FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.id",
            "SELECT * FROM products WHERE category = 'electronics' ORDER BY price DESC",
            "SELECT AVG(amount) FROM orders WHERE date >= '2024-01-01'",
            "SELECT c.name FROM customers c WHERE c.id IN (SELECT customer_id FROM orders WHERE amount > 1000)",
        ]
        
        for i, query in enumerate(queries):
            # Simulate different execution times based on complexity
            base_time = 0.2 + i * 0.3
            execution_time = base_time + np.random.normal(0, 0.1)
            
            synthetic_data.append({
                'query': query,
                'execution_time': max(0.1, execution_time)
            })
        
        # Add more synthetic examples
        for _ in range(50):
            length = np.random.randint(50, 500)
            joins = np.random.randint(0, 5)
            complexity = length * 0.001 + joins * 2.0
            execution_time = 0.1 + complexity * 0.1 + np.random.normal(0, 0.05)
            
            synthetic_data.append({
                'query': f"SELECT * FROM table{np.random.randint(1, 10)}",
                'execution_time': max(0.1, execution_time)
            })
        
        return synthetic_data

class QueryOptimizer:
    """AI-powered query optimization suggestions"""
    
    def __init__(self, performance_model: PerformancePredictionModel):
        self.performance_model = performance_model
        self.optimization_rules = self._load_optimization_rules()
    
    def suggest_optimizations(self, query: str) -> List[QueryOptimizationSuggestion]:
        """Generate optimization suggestions for a query"""
        suggestions = []
        
        # Get current performance prediction
        current_performance = self.performance_model.predict_performance(query)
        current_time = current_performance.get('predicted_execution_time', 1.0)
        
        # Apply optimization rules
        for rule in self.optimization_rules:
            if self._rule_applies(query, rule):
                optimized_query = self._apply_optimization(query, rule)
                
                # Predict optimized performance
                optimized_performance = self.performance_model.predict_performance(optimized_query)
                optimized_time = optimized_performance.get('predicted_execution_time', 1.0)
                
                # Calculate improvement
                speedup = max(1.0, current_time / optimized_time)
                
                if speedup > 1.1:  # Only suggest if >10% improvement
                    suggestions.append(QueryOptimizationSuggestion(
                        original_query=query,
                        optimized_query=optimized_query,
                        improvement_type=rule['type'],
                        estimated_speedup=speedup,
                        confidence=rule['confidence'],
                        explanation=rule['explanation']
                    ))
        
        return sorted(suggestions, key=lambda x: x.estimated_speedup, reverse=True)
    
    def _load_optimization_rules(self) -> List[Dict]:
        """Load query optimization rules"""
        return [
            {
                'type': 'add_index_hint',
                'pattern': r'WHERE\s+(\w+)\s*=',
                'optimization': lambda m, q: q.replace(m.group(0), f"{m.group(0)} /* INDEX HINT: Consider index on {m.group(1)} */"),
                'confidence': 0.8,
                'explanation': 'Adding an index on the WHERE clause column can significantly improve performance'
            },
            {
                'type': 'limit_results',
                'pattern': r'SELECT.*FROM.*(?!LIMIT)',
                'optimization': lambda m, q: q + ' LIMIT 1000' if 'LIMIT' not in q.upper() else q,
                'confidence': 0.9,
                'explanation': 'Adding LIMIT clause prevents accidentally retrieving too many rows'
            },
            {
                'type': 'select_specific_columns',
                'pattern': r'SELECT\s+\*\s+FROM',
                'optimization': lambda m, q: q.replace('SELECT *', 'SELECT id, name, created_at /* Specify needed columns */'),
                'confidence': 0.7,
                'explanation': 'Selecting specific columns instead of * reduces data transfer and improves performance'
            },
            {
                'type': 'optimize_join_order',
                'pattern': r'JOIN\s+(\w+)\s+ON',
                'optimization': lambda m, q: q + ' /* HINT: Ensure smaller table is on the right side of JOIN */',
                'confidence': 0.6,
                'explanation': 'Optimizing join order can improve query execution time'
            }
        ]
    
    def _rule_applies(self, query: str, rule: Dict) -> bool:
        """Check if optimization rule applies to query"""
        return bool(re.search(rule['pattern'], query, re.IGNORECASE))
    
    def _apply_optimization(self, query: str, rule: Dict) -> str:
        """Apply optimization rule to query"""
        match = re.search(rule['pattern'], query, re.IGNORECASE)
        if match:
            return rule['optimization'](match, query)
        return query

class BusinessInsightsGenerator:
    """AI-powered business insights from data patterns"""
    
    def __init__(self):
        self.insight_templates = self._load_insight_templates()
    
    def generate_insights(self, data_summary: Dict) -> List[BusinessInsight]:
        """Generate business insights from data patterns"""
        insights = []
        
        # Revenue trend insights
        if 'revenue_data' in data_summary:
            revenue_insight = self._analyze_revenue_trends(data_summary['revenue_data'])
            if revenue_insight:
                insights.append(revenue_insight)
        
        # Customer behavior insights
        if 'customer_data' in data_summary:
            customer_insight = self._analyze_customer_patterns(data_summary['customer_data'])
            if customer_insight:
                insights.append(customer_insight)
        
        # Product performance insights
        if 'product_data' in data_summary:
            product_insight = self._analyze_product_performance(data_summary['product_data'])
            if product_insight:
                insights.append(product_insight)
        
        # Operational efficiency insights
        if 'operational_data' in data_summary:
            ops_insight = self._analyze_operational_efficiency(data_summary['operational_data'])
            if ops_insight:
                insights.append(ops_insight)
        
        return insights
    
    def _analyze_revenue_trends(self, revenue_data: Dict) -> Optional[BusinessInsight]:
        """Analyze revenue trends and generate insights"""
        # Simulate revenue analysis
        monthly_growth = np.random.uniform(-5, 15)  # -5% to +15%
        
        if monthly_growth > 10:
            impact_level = "high"
            recommendations = [
                "Invest in scaling successful channels",
                "Expand to new market segments",
                "Increase marketing budget for high-performing campaigns"
            ]
        elif monthly_growth > 5:
            impact_level = "medium"
            recommendations = [
                "Optimize current growth strategies",
                "Focus on customer retention",
                "Analyze successful product categories"
            ]
        else:
            impact_level = "low"
            recommendations = [
                "Review pricing strategy",
                "Improve customer acquisition",
                "Analyze competitor activities"
            ]
        
        return BusinessInsight(
            insight_type="revenue_trend",
            title=f"Revenue Growth Analysis: {monthly_growth:.1f}% Monthly Growth",
            description=f"Current revenue trend shows {monthly_growth:.1f}% monthly growth rate.",
            data_points=[
                {"metric": "monthly_growth_rate", "value": monthly_growth},
                {"metric": "confidence_level", "value": 0.85}
            ],
            confidence=0.85,
            actionable_recommendations=recommendations,
            impact_level=impact_level
        )
    
    def _analyze_customer_patterns(self, customer_data: Dict) -> Optional[BusinessInsight]:
        """Analyze customer behavior patterns"""
        # Simulate customer analysis
        churn_rate = np.random.uniform(2, 12)  # 2% to 12%
        
        if churn_rate < 5:
            impact_level = "low"
            recommendations = [
                "Maintain current customer success programs",
                "Focus on upselling to satisfied customers"
            ]
        elif churn_rate < 8:
            impact_level = "medium"
            recommendations = [
                "Implement proactive customer outreach",
                "Improve onboarding process",
                "Analyze feedback from churned customers"
            ]
        else:
            impact_level = "high"
            recommendations = [
                "Urgent review of customer satisfaction",
                "Implement retention campaigns",
                "Analyze product-market fit"
            ]
        
        return BusinessInsight(
            insight_type="customer_behavior",
            title=f"Customer Retention Analysis: {churn_rate:.1f}% Churn Rate",
            description=f"Customer churn rate is {churn_rate:.1f}%, indicating {'good' if churn_rate < 5 else 'concerning'} retention.",
            data_points=[
                {"metric": "churn_rate", "value": churn_rate},
                {"metric": "confidence_level", "value": 0.78}
            ],
            confidence=0.78,
            actionable_recommendations=recommendations,
            impact_level=impact_level
        )
    
    def _analyze_product_performance(self, product_data: Dict) -> Optional[BusinessInsight]:
        """Analyze product performance patterns"""
        # Simulate product analysis
        top_performers = np.random.randint(3, 8)
        underperformers = np.random.randint(2, 6)
        
        return BusinessInsight(
            insight_type="product_performance",
            title=f"Product Portfolio Analysis: {top_performers} Top Performers Identified",
            description=f"Analysis reveals {top_performers} top-performing products and {underperformers} underperforming items.",
            data_points=[
                {"metric": "top_performers", "value": top_performers},
                {"metric": "underperformers", "value": underperformers}
            ],
            confidence=0.82,
            actionable_recommendations=[
                f"Focus marketing budget on {top_performers} top-performing products",
                f"Review strategy for {underperformers} underperforming items",
                "Analyze characteristics of successful products for future development"
            ],
            impact_level="medium"
        )
    
    def _analyze_operational_efficiency(self, operational_data: Dict) -> Optional[BusinessInsight]:
        """Analyze operational efficiency metrics"""
        # Simulate operational analysis
        efficiency_score = np.random.uniform(65, 95)
        
        return BusinessInsight(
            insight_type="operational_efficiency",
            title=f"Operational Efficiency Score: {efficiency_score:.1f}%",
            description=f"Current operational efficiency is {efficiency_score:.1f}%, with opportunities for improvement.",
            data_points=[
                {"metric": "efficiency_score", "value": efficiency_score},
                {"metric": "industry_benchmark", "value": 82.0}
            ],
            confidence=0.88,
            actionable_recommendations=[
                "Automate repetitive manual processes",
                "Optimize resource allocation",
                "Implement performance monitoring dashboards"
            ],
            impact_level="medium" if efficiency_score > 80 else "high"
        )
    
    def _load_insight_templates(self) -> List[Dict]:
        """Load business insight templates"""
        return [
            {
                'type': 'trend_analysis',
                'pattern': 'time_series',
                'confidence': 0.8
            },
            {
                'type': 'anomaly_detection',
                'pattern': 'outliers',
                'confidence': 0.9
            }
        ]

class MLAnalyticsEngine:
    """Main ML analytics engine coordinator"""
    
    def __init__(self):
        self.performance_model = PerformancePredictionModel()
        self.query_optimizer = QueryOptimizer(self.performance_model)
        self.insights_generator = BusinessInsightsGenerator()
        self.is_initialized = False
    
    def initialize(self) -> Dict:
        """Initialize the ML analytics engine"""
        print("Initializing ML Analytics Engine...")
        
        # Train performance model
        training_results = self.performance_model.train([])
        
        self.is_initialized = True
        
        return {
            'status': 'initialized',
            'performance_model': training_results,
            'timestamp': datetime.now().isoformat()
        }
    
    def analyze_query(self, query: str) -> Dict:
        """Complete ML analysis of a SQL query"""
        if not self.is_initialized:
            self.initialize()
        
        # Performance prediction
        performance = self.performance_model.predict_performance(query)
        
        # Optimization suggestions
        optimizations = self.query_optimizer.suggest_optimizations(query)
        
        return {
            'query': query,
            'performance_prediction': performance,
            'optimization_suggestions': [
                {
                    'type': opt.improvement_type,
                    'optimized_query': opt.optimized_query,
                    'estimated_speedup': opt.estimated_speedup,
                    'confidence': opt.confidence,
                    'explanation': opt.explanation
                }
                for opt in optimizations
            ],
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def generate_business_insights(self, data_context: Dict = None) -> List[Dict]:
        """Generate business insights from available data"""
        if not data_context:
            # Generate sample data context for demo
            data_context = {
                'revenue_data': {'monthly_values': [100000, 105000, 110000]},
                'customer_data': {'total_customers': 1500, 'active_customers': 1200},
                'product_data': {'total_products': 50, 'categories': 8},
                'operational_data': {'processes': 25, 'automated': 18}
            }
        
        insights = self.insights_generator.generate_insights(data_context)
        
        return [
            {
                'type': insight.insight_type,
                'title': insight.title,
                'description': insight.description,
                'confidence': insight.confidence,
                'impact_level': insight.impact_level,
                'recommendations': insight.actionable_recommendations,
                'data_points': insight.data_points
            }
            for insight in insights
        ]
    
    def get_ml_system_status(self) -> Dict:
        """Get status of ML system components"""
        return {
            'initialized': self.is_initialized,
            'performance_model_trained': self.performance_model.is_trained,
            'components': {
                'query_analyzer': 'active',
                'performance_predictor': 'active' if self.performance_model.is_trained else 'training',
                'query_optimizer': 'active',
                'insights_generator': 'active'
            },
            'last_updated': datetime.now().isoformat()
        }

# Global ML engine instance
ml_engine = MLAnalyticsEngine()

if __name__ == "__main__":
    # Test the ML analytics engine
    engine = MLAnalyticsEngine()
    
    # Initialize
    init_result = engine.initialize()
    print("Initialization:", init_result)
    
    # Test query analysis
    test_query = "SELECT c.name, COUNT(o.id) as order_count FROM customers c LEFT JOIN orders o ON c.id = o.customer_id WHERE c.created_at > '2024-01-01' GROUP BY c.id ORDER BY order_count DESC"
    
    analysis = engine.analyze_query(test_query)
    print("\nQuery Analysis:")
    print(f"Predicted execution time: {analysis['performance_prediction']['predicted_execution_time']:.3f}s")
    print(f"Performance category: {analysis['performance_prediction']['performance_category']}")
    print(f"Optimization suggestions: {len(analysis['optimization_suggestions'])}")
    
    # Test business insights
    insights = engine.generate_business_insights()
    print(f"\nGenerated {len(insights)} business insights")
    for insight in insights:
        print(f"- {insight['title']} (Impact: {insight['impact_level']})")