"""
Advanced SQL Optimizer and Analysis Engine
Provides performance analysis, optimization suggestions, and cost estimation
"""
import sqlparse
import re
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import sqlite3
import pandas as pd

class QueryComplexity(Enum):
    SIMPLE = "Simple"
    MODERATE = "Moderate"
    COMPLEX = "Complex"
    VERY_COMPLEX = "Very Complex"

class OptimizationLevel(Enum):
    LOW = "Low Priority"
    MEDIUM = "Medium Priority"
    HIGH = "High Priority"
    CRITICAL = "Critical"

@dataclass
class OptimizationSuggestion:
    category: str
    suggestion: str
    impact: OptimizationLevel
    explanation: str
    example: Optional[str] = None

@dataclass
class QueryAnalysis:
    complexity: QueryComplexity
    estimated_cost: float
    execution_time: float
    row_count: int
    suggestions: List[OptimizationSuggestion]
    performance_score: int  # 0-100
    readability_score: int  # 0-100

class SQLOptimizer:
    def __init__(self, database_manager=None):
        self.db_manager = database_manager
        
    def analyze_query(self, sql_query: str, execution_result: Dict = None) -> QueryAnalysis:
        """Comprehensive SQL query analysis"""
        
        # Parse the SQL
        parsed = sqlparse.parse(sql_query)[0]
        tokens = list(parsed.flatten())
        
        # Basic metrics
        complexity = self._assess_complexity(sql_query, tokens)
        estimated_cost = self._estimate_cost(sql_query, tokens)
        
        # Get execution metrics if available
        execution_time = execution_result.get('execution_time', 0) if execution_result else 0
        row_count = execution_result.get('row_count', 0) if execution_result else 0
        
        # Generate optimization suggestions
        suggestions = self._generate_suggestions(sql_query, tokens, execution_result)
        
        # Calculate scores
        performance_score = self._calculate_performance_score(sql_query, execution_time, row_count)
        readability_score = self._calculate_readability_score(sql_query, tokens)
        
        return QueryAnalysis(
            complexity=complexity,
            estimated_cost=estimated_cost,
            execution_time=execution_time,
            row_count=row_count,
            suggestions=suggestions,
            performance_score=performance_score,
            readability_score=readability_score
        )
    
    def _assess_complexity(self, sql_query: str, tokens: List) -> QueryComplexity:
        """Assess query complexity based on various factors"""
        
        complexity_score = 0
        sql_upper = sql_query.upper()
        
        # Check for complex operations
        if 'JOIN' in sql_upper:
            join_count = sql_upper.count('JOIN')
            complexity_score += join_count * 2
        
        if 'SUBQUERY' in sql_upper or '(' in sql_query:
            subquery_count = sql_query.count('SELECT') - 1
            complexity_score += subquery_count * 3
        
        if 'UNION' in sql_upper:
            complexity_score += 3
        
        if 'WINDOW' in sql_upper or 'OVER' in sql_upper:
            complexity_score += 4
        
        if 'WITH' in sql_upper:  # CTE
            complexity_score += 2
        
        # Check for aggregations
        agg_functions = ['SUM', 'COUNT', 'AVG', 'MAX', 'MIN', 'GROUP BY']
        for func in agg_functions:
            if func in sql_upper:
                complexity_score += 1
        
        # Determine complexity level
        if complexity_score <= 2:
            return QueryComplexity.SIMPLE
        elif complexity_score <= 5:
            return QueryComplexity.MODERATE
        elif complexity_score <= 10:
            return QueryComplexity.COMPLEX
        else:
            return QueryComplexity.VERY_COMPLEX
    
    def _estimate_cost(self, sql_query: str, tokens: List) -> float:
        """Estimate query execution cost (simplified model)"""
        
        base_cost = 1.0
        sql_upper = sql_query.upper()
        
        # Table scan costs
        table_count = sql_upper.count('FROM') + sql_upper.count('JOIN')
        base_cost += table_count * 0.5
        
        # Join costs (exponential)
        join_count = sql_upper.count('JOIN')
        if join_count > 0:
            base_cost += (2 ** join_count) * 0.3
        
        # Subquery costs
        subquery_count = sql_query.count('SELECT') - 1
        base_cost += subquery_count * 2.0
        
        # Aggregation costs
        if 'GROUP BY' in sql_upper:
            base_cost += 1.5
        
        # Sorting costs
        if 'ORDER BY' in sql_upper:
            base_cost += 1.0
        
        # Window function costs
        if 'OVER' in sql_upper:
            base_cost += 2.0
        
        return round(base_cost, 2)
    
    def _generate_suggestions(self, sql_query: str, tokens: List, execution_result: Dict = None) -> List[OptimizationSuggestion]:
        """Generate optimization suggestions based on query analysis"""
        
        suggestions = []
        sql_upper = sql_query.upper()
        
        # Check for SELECT *
        if 'SELECT *' in sql_upper:
            suggestions.append(OptimizationSuggestion(
                category="Column Selection",
                suggestion="Avoid SELECT * - specify only needed columns",
                impact=OptimizationLevel.MEDIUM,
                explanation="SELECT * retrieves all columns, which increases I/O and network overhead",
                example="SELECT id, name, email FROM users -- instead of SELECT * FROM users"
            ))
        
        # Check for missing WHERE clause
        if 'WHERE' not in sql_upper and 'SELECT' in sql_upper:
            suggestions.append(OptimizationSuggestion(
                category="Filtering",
                suggestion="Consider adding WHERE clause to limit results",
                impact=OptimizationLevel.HIGH,
                explanation="Unfiltered queries can return large datasets and impact performance",
                example="SELECT * FROM orders WHERE order_date >= '2024-01-01'"
            ))
        
        # Check for inefficient JOINs
        if 'JOIN' in sql_upper and 'WHERE' not in sql_upper:
            suggestions.append(OptimizationSuggestion(
                category="JOIN Optimization",
                suggestion="Add WHERE conditions to reduce JOIN result set",
                impact=OptimizationLevel.HIGH,
                explanation="Filtering before JOINs reduces the amount of data being joined",
                example="Add WHERE conditions on the most selective columns first"
            ))
        
        # Check for ORDER BY without LIMIT
        if 'ORDER BY' in sql_upper and 'LIMIT' not in sql_upper:
            suggestions.append(OptimizationSuggestion(
                category="Result Limiting",
                suggestion="Consider adding LIMIT clause with ORDER BY",
                impact=OptimizationLevel.MEDIUM,
                explanation="ORDER BY without LIMIT sorts entire result set unnecessarily",
                example="ORDER BY column_name LIMIT 100"
            ))
        
        # Check for potential index usage
        if 'WHERE' in sql_upper:
            suggestions.append(OptimizationSuggestion(
                category="Indexing",
                suggestion="Ensure indexes exist on WHERE clause columns",
                impact=OptimizationLevel.HIGH,
                explanation="Proper indexes dramatically improve WHERE clause performance",
                example="CREATE INDEX idx_column_name ON table_name(column_name)"
            ))
        
        # Check for subqueries that could be JOINs
        if sql_query.count('SELECT') > 1 and 'IN (' in sql_upper:
            suggestions.append(OptimizationSuggestion(
                category="Query Structure",
                suggestion="Consider converting IN subqueries to JOINs",
                impact=OptimizationLevel.MEDIUM,
                explanation="JOINs are often more efficient than correlated subqueries",
                example="Use INNER JOIN instead of WHERE column IN (SELECT ...)"
            ))
        
        # Performance-based suggestions
        if execution_result and execution_result.get('execution_time', 0) > 1.0:
            suggestions.append(OptimizationSuggestion(
                category="Performance",
                suggestion="Query execution time is high - consider optimization",
                impact=OptimizationLevel.CRITICAL,
                explanation=f"Execution time: {execution_result['execution_time']:.3f}s is above recommended threshold",
                example="Review indexes, query structure, and data volumes"
            ))
        
        # Check for potential data type issues
        if "'" in sql_query and 'CAST' not in sql_upper:
            suggestions.append(OptimizationSuggestion(
                category="Data Types",
                suggestion="Ensure proper data type handling in comparisons",
                impact=OptimizationLevel.LOW,
                explanation="Implicit type conversions can prevent index usage",
                example="Use proper data types: WHERE date_column = DATE('2024-01-01')"
            ))
        
        return suggestions
    
    def _calculate_performance_score(self, sql_query: str, execution_time: float, row_count: int) -> int:
        """Calculate performance score (0-100, higher is better)"""
        
        score = 100
        sql_upper = sql_query.upper()
        
        # Deduct points for performance issues
        if 'SELECT *' in sql_upper:
            score -= 15
        
        if 'WHERE' not in sql_upper:
            score -= 25
        
        if execution_time > 1.0:
            score -= min(30, int(execution_time * 10))
        
        if 'ORDER BY' in sql_upper and 'LIMIT' not in sql_upper:
            score -= 10
        
        # Deduct for complexity without optimization
        join_count = sql_upper.count('JOIN')
        if join_count > 2:
            score -= (join_count - 2) * 5
        
        # Bonus for good practices
        if 'LIMIT' in sql_upper:
            score += 5
        
        if 'WITH' in sql_upper:  # Using CTEs
            score += 5
        
        return max(0, min(100, score))
    
    def _calculate_readability_score(self, sql_query: str, tokens: List) -> int:
        """Calculate readability score (0-100, higher is better)"""
        
        score = 100
        lines = sql_query.strip().split('\n')
        
        # Check formatting
        if len(lines) == 1 and len(sql_query) > 100:
            score -= 20  # Single long line
        
        # Check for proper indentation
        has_indentation = any(line.startswith('    ') or line.startswith('\t') for line in lines)
        if not has_indentation and len(lines) > 3:
            score -= 15
        
        # Check for comments
        if '--' in sql_query or '/*' in sql_query:
            score += 10
        
        # Check for consistent keyword casing
        keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'GROUP BY', 'ORDER BY']
        keyword_cases = []
        for keyword in keywords:
            if keyword in sql_query:
                keyword_cases.append(keyword.isupper())
            elif keyword.lower() in sql_query:
                keyword_cases.append(False)
        
        if keyword_cases and not all(keyword_cases) and not all(not case for case in keyword_cases):
            score -= 10  # Inconsistent casing
        
        # Check for meaningful aliases
        if ' AS ' in sql_query.upper():
            score += 5
        
        return max(0, min(100, score))
    
    def get_optimization_report(self, query_analysis: QueryAnalysis) -> str:
        """Generate a comprehensive optimization report"""
        
        report = f"""
# 📊 SQL Query Analysis Report

## 🎯 Overall Assessment
- **Complexity**: {query_analysis.complexity.value}
- **Estimated Cost**: {query_analysis.estimated_cost}/10
- **Performance Score**: {query_analysis.performance_score}/100
- **Readability Score**: {query_analysis.readability_score}/100

## ⚡ Execution Metrics
- **Execution Time**: {query_analysis.execution_time:.3f} seconds
- **Rows Returned**: {query_analysis.row_count:,}

## 🔧 Optimization Suggestions

"""
        
        if not query_analysis.suggestions:
            report += "✅ **No major optimization issues found!** Your query follows good practices.\n"
        else:
            for i, suggestion in enumerate(query_analysis.suggestions, 1):
                impact_emoji = {
                    OptimizationLevel.LOW: "🟡",
                    OptimizationLevel.MEDIUM: "🟠", 
                    OptimizationLevel.HIGH: "🔴",
                    OptimizationLevel.CRITICAL: "🚨"
                }.get(suggestion.impact, "⚪")
                
                report += f"""
### {i}. {suggestion.category} {impact_emoji}
**Issue**: {suggestion.suggestion}
**Impact**: {suggestion.impact.value}
**Explanation**: {suggestion.explanation}
"""
                if suggestion.example:
                    report += f"**Example**: `{suggestion.example}`\n"
        
        return report
    
    def benchmark_query(self, sql_query: str, iterations: int = 5) -> Dict:
        """Benchmark query performance over multiple executions"""
        
        if not self.db_manager:
            return {"error": "No database manager available for benchmarking"}
        
        execution_times = []
        results = []
        
        for i in range(iterations):
            start_time = time.time()
            result = self.db_manager.execute_query(sql_query)
            end_time = time.time()
            
            if result['success']:
                execution_times.append(end_time - start_time)
                results.append(result)
            else:
                return {"error": f"Query failed: {result['error']}"}
        
        return {
            "success": True,
            "iterations": iterations,
            "avg_execution_time": sum(execution_times) / len(execution_times),
            "min_execution_time": min(execution_times),
            "max_execution_time": max(execution_times),
            "std_deviation": pd.Series(execution_times).std(),
            "all_times": execution_times,
            "row_count": results[0]['row_count'] if results else 0
        }

def test_optimizer():
    """Test the SQL optimizer functionality"""
    print("🧪 Testing SQL Optimizer...")
    
    optimizer = SQLOptimizer()
    
    # Test query with potential issues
    test_query = """
    SELECT * 
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    ORDER BY o.order_date
    """
    
    # Mock execution result
    mock_result = {
        'success': True,
        'execution_time': 0.123,
        'row_count': 150
    }
    
    analysis = optimizer.analyze_query(test_query, mock_result)
    
    print(f"✅ Query analyzed successfully!")
    print(f"   Complexity: {analysis.complexity.value}")
    print(f"   Performance Score: {analysis.performance_score}/100")
    print(f"   Suggestions: {len(analysis.suggestions)}")
    
    # Generate report
    report = optimizer.get_optimization_report(analysis)
    print("\n📋 Sample Report Generated")
    
    return analysis

if __name__ == "__main__":
    test_optimizer()
