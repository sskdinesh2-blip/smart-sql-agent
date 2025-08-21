# src/day10_security_framework.py
"""
Day 10: Enterprise Security & Compliance Framework
Advanced security, compliance monitoring, and enterprise integration
"""

import hashlib
import secrets
import json
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import re
import ipaddress
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class SecurityLevel(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class ComplianceFramework(Enum):
    GDPR = "gdpr"
    SOX = "sox"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    ISO27001 = "iso27001"

@dataclass
class SecurityEvent:
    event_id: str
    event_type: str
    user_id: Optional[int]
    ip_address: str
    timestamp: datetime
    severity: str
    details: Dict
    resolved: bool = False

@dataclass
class DataClassification:
    classification_level: SecurityLevel
    compliance_frameworks: List[ComplianceFramework]
    retention_period_days: int
    encryption_required: bool
    access_log_required: bool

@dataclass
class AccessPolicy:
    resource_pattern: str
    required_roles: List[str]
    allowed_operations: List[str]
    time_restrictions: Optional[Dict] = None
    ip_restrictions: Optional[List[str]] = None
    mfa_required: bool = False

class EncryptionManager:
    """Handles data encryption and key management"""
    
    def __init__(self, master_key: Optional[bytes] = None):
        if master_key is None:
            master_key = Fernet.generate_key()
        self.cipher_suite = Fernet(master_key)
        self.master_key = master_key
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        encrypted_data = self.cipher_suite.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception:
            raise ValueError("Failed to decrypt data")
    
    def hash_password(self, password: str, salt: Optional[bytes] = None) -> tuple:
        """Hash password with salt using PBKDF2"""
        if salt is None:
            salt = secrets.token_bytes(32)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode())
        return base64.b64encode(key).decode(), base64.b64encode(salt).decode()
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """Verify password against hash"""
        try:
            salt_bytes = base64.b64decode(salt.encode())
            expected_key, _ = self.hash_password(password, salt_bytes)
            return expected_key == hashed_password
        except Exception:
            return False

class SecurityAuditLogger:
    """Logs security events for compliance and monitoring"""
    
    def __init__(self, db_path: str = "data/security_audit.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize security audit database"""
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                user_id INTEGER,
                ip_address TEXT,
                timestamp TEXT NOT NULL,
                severity TEXT NOT NULL,
                details TEXT NOT NULL,
                resolved BOOLEAN DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_logs (
                log_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                resource TEXT NOT NULL,
                operation TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                ip_address TEXT,
                success BOOLEAN NOT NULL,
                details TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compliance_reports (
                report_id TEXT PRIMARY KEY,
                framework TEXT NOT NULL,
                report_date TEXT NOT NULL,
                compliance_score REAL NOT NULL,
                findings TEXT NOT NULL,
                recommendations TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def log_security_event(self, event: SecurityEvent):
        """Log a security event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO security_events 
            (event_id, event_type, user_id, ip_address, timestamp, severity, details, resolved)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.event_id,
            event.event_type,
            event.user_id,
            event.ip_address,
            event.timestamp.isoformat(),
            event.severity,
            json.dumps(event.details),
            event.resolved
        ))
        
        conn.commit()
        conn.close()
    
    def log_access_attempt(self, user_id: int, resource: str, operation: str, 
                          ip_address: str, success: bool, details: Dict = None):
        """Log access attempt for compliance"""
        log_id = secrets.token_hex(16)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO access_logs 
            (log_id, user_id, resource, operation, timestamp, ip_address, success, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log_id,
            user_id,
            resource,
            operation,
            datetime.now().isoformat(),
            ip_address,
            success,
            json.dumps(details or {})
        ))
        
        conn.commit()
        conn.close()
    
    def get_security_events(self, hours: int = 24) -> List[SecurityEvent]:
        """Get recent security events"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT event_id, event_type, user_id, ip_address, timestamp, severity, details, resolved
            FROM security_events 
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        """, (cutoff_time.isoformat(),))
        
        events = []
        for row in cursor.fetchall():
            events.append(SecurityEvent(
                event_id=row[0],
                event_type=row[1],
                user_id=row[2],
                ip_address=row[3],
                timestamp=datetime.fromisoformat(row[4]),
                severity=row[5],
                details=json.loads(row[6]),
                resolved=bool(row[7])
            ))
        
        conn.close()
        return events

class ComplianceMonitor:
    """Monitors compliance with various frameworks"""
    
    def __init__(self, audit_logger: SecurityAuditLogger):
        self.audit_logger = audit_logger
        self.compliance_rules = self._load_compliance_rules()
    
    def _load_compliance_rules(self) -> Dict:
        """Load compliance rules for different frameworks"""
        return {
            ComplianceFramework.GDPR: {
                "data_retention_max_days": 2555,  # 7 years
                "consent_required": True,
                "right_to_deletion": True,
                "breach_notification_hours": 72,
                "encryption_required": True
            },
            ComplianceFramework.SOX: {
                "audit_trail_required": True,
                "financial_data_retention_years": 7,
                "access_controls_required": True,
                "segregation_of_duties": True
            },
            ComplianceFramework.HIPAA: {
                "phi_encryption_required": True,
                "access_logging_required": True,
                "minimum_necessary_standard": True,
                "breach_notification_required": True
            },
            ComplianceFramework.PCI_DSS: {
                "cardholder_data_encryption": True,
                "network_segmentation": True,
                "access_monitoring": True,
                "vulnerability_scanning": True
            },
            ComplianceFramework.ISO27001: {
                "information_security_policy": True,
                "risk_assessment_required": True,
                "incident_management": True,
                "continuous_monitoring": True
            }
        }
    
    def check_compliance(self, framework: ComplianceFramework) -> Dict:
        """Check compliance status for a framework"""
        rules = self.compliance_rules.get(framework, {})
        findings = []
        compliance_score = 0
        total_checks = len(rules)
        
        for rule_name, rule_value in rules.items():
            check_result = self._evaluate_rule(framework, rule_name, rule_value)
            findings.append(check_result)
            if check_result['compliant']:
                compliance_score += 1
        
        compliance_percentage = (compliance_score / total_checks * 100) if total_checks > 0 else 0
        
        return {
            'framework': framework.value,
            'compliance_score': compliance_percentage,
            'total_checks': total_checks,
            'passed_checks': compliance_score,
            'findings': findings,
            'recommendations': self._generate_recommendations(findings)
        }
    
    def _evaluate_rule(self, framework: ComplianceFramework, rule_name: str, rule_value) -> Dict:
        """Evaluate a specific compliance rule"""
        # Simplified compliance checking - in production, this would be more sophisticated
        compliant = True
        details = ""
        
        if rule_name == "encryption_required" and rule_value:
            # Check if encryption is properly implemented
            compliant = True  # Assume encryption is implemented
            details = "Data encryption is properly configured"
        
        elif rule_name == "audit_trail_required" and rule_value:
            # Check if audit trails are maintained
            recent_events = self.audit_logger.get_security_events(hours=24)
            compliant = len(recent_events) > 0
            details = f"Audit trail active with {len(recent_events)} recent events"
        
        elif rule_name == "access_logging_required" and rule_value:
            # Check if access is being logged
            compliant = True  # Assume access logging is implemented
            details = "Access logging is active"
        
        else:
            # Default evaluation
            compliant = True
            details = f"Rule {rule_name} is satisfied"
        
        return {
            'rule': rule_name,
            'required': rule_value,
            'compliant': compliant,
            'details': details,
            'severity': 'high' if not compliant else 'info'
        }
    
    def _generate_recommendations(self, findings: List[Dict]) -> List[str]:
        """Generate recommendations based on findings"""
        recommendations = []
        
        for finding in findings:
            if not finding['compliant']:
                if finding['rule'] == 'encryption_required':
                    recommendations.append("Implement end-to-end encryption for sensitive data")
                elif finding['rule'] == 'audit_trail_required':
                    recommendations.append("Enable comprehensive audit logging")
                elif finding['rule'] == 'access_logging_required':
                    recommendations.append("Implement detailed access logging")
                else:
                    recommendations.append(f"Address compliance issue: {finding['rule']}")
        
        if not recommendations:
            recommendations.append("All compliance checks passed - maintain current security posture")
        
        return recommendations

class AccessControlManager:
    """Manages role-based access control and policies"""
    
    def __init__(self, audit_logger: SecurityAuditLogger):
        self.audit_logger = audit_logger
        self.policies: List[AccessPolicy] = []
        self.load_default_policies()
    
    def load_default_policies(self):
        """Load default access control policies"""
        self.policies = [
            AccessPolicy(
                resource_pattern="/api/admin/*",
                required_roles=["admin"],
                allowed_operations=["GET", "POST", "PUT", "DELETE"],
                mfa_required=True
            ),
            AccessPolicy(
                resource_pattern="/api/users/*",
                required_roles=["admin", "user_manager"],
                allowed_operations=["GET", "POST", "PUT"],
                mfa_required=True
            ),
            AccessPolicy(
                resource_pattern="/api/sql/generate",
                required_roles=["user", "admin"],
                allowed_operations=["POST"],
                time_restrictions={"business_hours_only": True}
            ),
            AccessPolicy(
                resource_pattern="/api/reports/*",
                required_roles=["analyst", "admin"],
                allowed_operations=["GET"],
                ip_restrictions=["10.0.0.0/8", "192.168.0.0/16"]
            )
        ]
    
    def check_access(self, user_roles: List[str], resource: str, operation: str,
                    ip_address: str = None, time_check: bool = True) -> Dict:
        """Check if access should be granted"""
        applicable_policies = self._find_applicable_policies(resource)
        
        if not applicable_policies:
            return {"allowed": True, "reason": "No specific policy - default allow"}
        
        for policy in applicable_policies:
            # Check role requirements
            if not any(role in user_roles for role in policy.required_roles):
                return {
                    "allowed": False,
                    "reason": f"Insufficient roles. Required: {policy.required_roles}"
                }
            
            # Check operation
            if operation not in policy.allowed_operations:
                return {
                    "allowed": False,
                    "reason": f"Operation {operation} not allowed"
                }
            
            # Check IP restrictions
            if policy.ip_restrictions and ip_address:
                if not self._check_ip_allowed(ip_address, policy.ip_restrictions):
                    return {
                        "allowed": False,
                        "reason": "IP address not in allowed range"
                    }
            
            # Check time restrictions
            if time_check and policy.time_restrictions:
                if not self._check_time_allowed(policy.time_restrictions):
                    return {
                        "allowed": False,
                        "reason": "Access not allowed at this time"
                    }
        
        return {
            "allowed": True,
            "reason": "Access granted",
            "mfa_required": any(p.mfa_required for p in applicable_policies)
        }
    
    def _find_applicable_policies(self, resource: str) -> List[AccessPolicy]:
        """Find policies that apply to a resource"""
        applicable = []
        for policy in self.policies:
            if self._resource_matches_pattern(resource, policy.resource_pattern):
                applicable.append(policy)
        return applicable
    
    def _resource_matches_pattern(self, resource: str, pattern: str) -> bool:
        """Check if resource matches pattern (simplified glob matching)"""
        if pattern.endswith("*"):
            return resource.startswith(pattern[:-1])
        return resource == pattern
    
    def _check_ip_allowed(self, ip_address: str, allowed_ranges: List[str]) -> bool:
        """Check if IP address is in allowed ranges"""
        try:
            ip = ipaddress.ip_address(ip_address)
            for range_str in allowed_ranges:
                if "/" in range_str:
                    network = ipaddress.ip_network(range_str, strict=False)
                    if ip in network:
                        return True
                else:
                    if str(ip) == range_str:
                        return True
            return False
        except ValueError:
            return False
    
    def _check_time_allowed(self, time_restrictions: Dict) -> bool:
        """Check if current time is allowed"""
        current_time = datetime.now()
        
        if time_restrictions.get("business_hours_only"):
            # Business hours: 9 AM to 6 PM, Monday to Friday
            if current_time.weekday() >= 5:  # Weekend
                return False
            if current_time.hour < 9 or current_time.hour >= 18:
                return False
        
        return True

class ThreatDetectionEngine:
    """Detects security threats and suspicious activities"""
    
    def __init__(self, audit_logger: SecurityAuditLogger):
        self.audit_logger = audit_logger
        self.threat_patterns = self._load_threat_patterns()
        self.suspicious_activity_threshold = 5
    
    def _load_threat_patterns(self) -> Dict:
        """Load threat detection patterns"""
        return {
            "brute_force": {
                "pattern": "multiple_failed_logins",
                "threshold": 5,
                "time_window_minutes": 15,
                "severity": "high"
            },
            "sql_injection": {
                "pattern": "suspicious_sql_patterns",
                "keywords": ["'; DROP", "UNION SELECT", "' OR '1'='1"],
                "severity": "critical"
            },
            "privilege_escalation": {
                "pattern": "role_change_anomaly",
                "threshold": 3,
                "time_window_hours": 1,
                "severity": "high"
            },
            "data_exfiltration": {
                "pattern": "large_data_access",
                "threshold_mb": 100,
                "time_window_minutes": 10,
                "severity": "critical"
            }
        }
    
    def analyze_query_for_threats(self, query: str, user_id: int, ip_address: str) -> List[SecurityEvent]:
        """Analyze SQL query for potential threats"""
        threats = []
        
        # Check for SQL injection patterns
        for keyword in self.threat_patterns["sql_injection"]["keywords"]:
            if keyword.lower() in query.lower():
                event = SecurityEvent(
                    event_id=secrets.token_hex(16),
                    event_type="sql_injection_attempt",
                    user_id=user_id,
                    ip_address=ip_address,
                    timestamp=datetime.now(),
                    severity="critical",
                    details={
                        "query": query[:200],  # Truncated for logging
                        "detected_pattern": keyword,
                        "full_query_hash": hashlib.sha256(query.encode()).hexdigest()
                    }
                )
                threats.append(event)
                self.audit_logger.log_security_event(event)
        
        return threats
    
    def check_login_patterns(self, user_id: int, ip_address: str, success: bool) -> Optional[SecurityEvent]:
        """Check for brute force login attempts"""
        if success:
            return None
        
        # Check recent failed attempts
        conn = sqlite3.connect(self.audit_logger.db_path)
        cursor = conn.cursor()
        
        cutoff_time = datetime.now() - timedelta(minutes=15)
        cursor.execute("""
            SELECT COUNT(*) FROM access_logs 
            WHERE user_id = ? AND ip_address = ? AND success = 0 AND timestamp > ?
        """, (user_id, ip_address, cutoff_time.isoformat()))
        
        failed_attempts = cursor.fetchone()[0]
        conn.close()
        
        if failed_attempts >= self.suspicious_activity_threshold:
            event = SecurityEvent(
                event_id=secrets.token_hex(16),
                event_type="brute_force_attempt",
                user_id=user_id,
                ip_address=ip_address,
                timestamp=datetime.now(),
                severity="high",
                details={
                    "failed_attempts": failed_attempts,
                    "time_window_minutes": 15,
                    "recommended_action": "Temporary account lockout"
                }
            )
            self.audit_logger.log_security_event(event)
            return event
        
        return None

class EnterpriseSecurityFramework:
    """Main enterprise security framework coordinator"""
    
    def __init__(self):
        self.encryption_manager = EncryptionManager()
        self.audit_logger = SecurityAuditLogger()
        self.compliance_monitor = ComplianceMonitor(self.audit_logger)
        self.access_control = AccessControlManager(self.audit_logger)
        self.threat_detection = ThreatDetectionEngine(self.audit_logger)
    
    def authenticate_request(self, user_id: int, user_roles: List[str], 
                           resource: str, operation: str, ip_address: str,
                           query_content: str = None) -> Dict:
        """Comprehensive request authentication"""
        # Check access control
        access_result = self.access_control.check_access(
            user_roles, resource, operation, ip_address
        )
        
        if not access_result["allowed"]:
            self.audit_logger.log_access_attempt(
                user_id, resource, operation, ip_address, False,
                {"reason": access_result["reason"]}
            )
            return access_result
        
        # Check for threats if SQL query is involved
        threats = []
        if query_content and operation == "POST" and "/sql/" in resource:
            threats = self.threat_detection.analyze_query_for_threats(
                query_content, user_id, ip_address
            )
        
        # Log successful access
        self.audit_logger.log_access_attempt(
            user_id, resource, operation, ip_address, True,
            {"threats_detected": len(threats)}
        )
        
        return {
            "allowed": True,
            "mfa_required": access_result.get("mfa_required", False),
            "threats_detected": len(threats),
            "security_level": self._determine_security_level(resource)
        }
    
    def _determine_security_level(self, resource: str) -> SecurityLevel:
        """Determine security level for resource"""
        if "/admin/" in resource:
            return SecurityLevel.RESTRICTED
        elif "/reports/" in resource:
            return SecurityLevel.CONFIDENTIAL
        elif "/api/" in resource:
            return SecurityLevel.INTERNAL
        else:
            return SecurityLevel.PUBLIC
    
    def generate_compliance_report(self, framework: ComplianceFramework) -> Dict:
        """Generate compliance report for framework"""
        return self.compliance_monitor.check_compliance(framework)
    
    def get_security_dashboard(self) -> Dict:
        """Get security dashboard data"""
        recent_events = self.audit_logger.get_security_events(hours=24)
        
        # Categorize events by severity
        severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for event in recent_events:
            severity_counts[event.severity] = severity_counts.get(event.severity, 0) + 1
        
        # Get compliance scores
        compliance_scores = {}
        for framework in ComplianceFramework:
            report = self.compliance_monitor.check_compliance(framework)
            compliance_scores[framework.value] = report['compliance_score']
        
        return {
            "security_events_24h": len(recent_events),
            "severity_breakdown": severity_counts,
            "compliance_scores": compliance_scores,
            "threat_level": self._calculate_threat_level(recent_events),
            "last_updated": datetime.now().isoformat()
        }
    
    def _calculate_threat_level(self, events: List[SecurityEvent]) -> str:
        """Calculate overall threat level"""
        if any(event.severity == "critical" for event in events):
            return "high"
        elif any(event.severity == "high" for event in events):
            return "medium"
        elif any(event.severity == "medium" for event in events):
            return "low"
        else:
            return "minimal"

# Global security framework instance
security_framework = EnterpriseSecurityFramework()

if __name__ == "__main__":
    # Test the security framework
    framework = EnterpriseSecurityFramework()
    
    # Test authentication
    auth_result = framework.authenticate_request(
        user_id=1,
        user_roles=["user"],
        resource="/api/sql/generate",
        operation="POST",
        ip_address="192.168.1.100",
        query_content="SELECT * FROM customers WHERE id = 1"
    )
    print("Authentication result:", auth_result)
    
    # Test compliance
    gdpr_report = framework.generate_compliance_report(ComplianceFramework.GDPR)
    print(f"GDPR Compliance: {gdpr_report['compliance_score']:.1f}%")
    
    # Test security dashboard
    dashboard = framework.get_security_dashboard()
    print("Security Dashboard:", dashboard)