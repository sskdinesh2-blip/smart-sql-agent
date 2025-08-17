# src/auth_system.py
"""
User Authentication and Authorization System
Multi-user support with role-based access control
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import sqlite3
import hashlib
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, List
import secrets

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

class User(BaseModel):
    id: Optional[int] = None
    username: str
    email: str
    role: str = "user"  # admin, user, viewer
    created_at: Optional[str] = None
    is_active: bool = True

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "user"

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class AuthSystem:
    def __init__(self, db_path="data/users.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize user database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Create default admin user if not exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        if cursor.fetchone()[0] == 0:
            admin_password = self.hash_password("admin123")
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            """, ("admin", "admin@sqlagent.com", admin_password, "admin"))
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password: str) -> str:
        """Hash password with salt"""
        return hashlib.pbkdf2_hmac('sha256', 
                                 password.encode('utf-8'), 
                                 b'salt', 
                                 100000).hex()
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return self.hash_password(password) == password_hash
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None
    
    def create_user(self, user_data: UserCreate) -> User:
        """Create new user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            password_hash = self.hash_password(user_data.password)
            
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            """, (user_data.username, user_data.email, password_hash, user_data.role))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            # Return created user
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            
            return User(
                id=row[0],
                username=row[1],
                email=row[2],
                role=row[4],
                created_at=row[5],
                is_active=bool(row[6])
            )
            
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=400,
                detail="Username or email already exists"
            )
        finally:
            conn.close()
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user credentials"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = ? AND is_active = 1", (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row and self.verify_password(password, row[3]):
            return User(
                id=row[0],
                username=row[1],
                email=row[2],
                role=row[4],
                created_at=row[5],
                is_active=bool(row[6])
            )
        return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE id = ? AND is_active = 1", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(
                id=row[0],
                username=row[1],
                email=row[2],
                role=row[4],
                created_at=row[5],
                is_active=bool(row[6])
            )
        return None
    
    def get_all_users(self) -> List[User]:
        """Get all active users"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE is_active = 1 ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        return [User(
            id=row[0],
            username=row[1],
            email=row[2],
            role=row[4],
            created_at=row[5],
            is_active=bool(row[6])
        ) for row in rows]

# Global auth instance
auth_system = AuthSystem()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    try:
        payload = auth_system.verify_token(credentials.credentials)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = auth_system.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_role(required_role: str):
    """Decorator to require specific role"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        role_hierarchy = {"viewer": 1, "user": 2, "admin": 3}
        
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(required_role, 999)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_role}"
            )
        return current_user
    
    return role_checker

# Test the auth system
if __name__ == "__main__":
    auth = AuthSystem()
    
    # Test user creation
    test_user = UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        role="user"
    )
    
    try:
        user = auth.create_user(test_user)
        print(f"Created user: {user.username}")
        
        # Test authentication
        auth_user = auth.authenticate_user("testuser", "testpass123")
        if auth_user:
            print(f"Authentication successful: {auth_user.username}")
            
            # Test token creation
            token = auth.create_access_token({"sub": auth_user.id})
            print(f"Generated token: {token[:50]}...")
            
            # Test token verification
            payload = auth.verify_token(token)
            print(f"Token verified: {payload}")
        else:
            print("Authentication failed")
            
    except Exception as e:
        print(f"Error: {e}")