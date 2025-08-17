# src/team_collaboration.py
"""
Team Collaboration Features
Shared queries, projects, comments, and team management
"""

import streamlit as st
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from auth_system import User, get_current_user
import pandas as pd

@dataclass
class Project:
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    owner_id: int = 0
    created_at: Optional[str] = None
    team_members: List[str] = None
    status: str = "active"  # active, archived, completed

@dataclass
class SharedQuery:
    id: Optional[int] = None
    title: str = ""
    sql_query: str = ""
    description: str = ""
    project_id: Optional[int] = None
    created_by: int = 0
    created_at: Optional[str] = None
    tags: List[str] = None
    is_public: bool = False
    execution_count: int = 0

@dataclass
class Comment:
    id: Optional[int] = None
    content: str = ""
    query_id: int = 0
    user_id: int = 0
    username: str = ""
    created_at: Optional[str] = None

class TeamCollaboration:
    def __init__(self, db_path="data/collaboration.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize collaboration database"""
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                owner_id INTEGER NOT NULL,
                team_members TEXT,  -- JSON array of user IDs
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Shared queries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shared_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                sql_query TEXT NOT NULL,
                description TEXT,
                project_id INTEGER,
                created_by INTEGER NOT NULL,
                tags TEXT,  -- JSON array of tags
                is_public BOOLEAN DEFAULT 0,
                execution_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)
        
        # Comments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                query_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (query_id) REFERENCES shared_queries (id)
            )
        """)
        
        # Query executions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                execution_time REAL,
                result_rows INTEGER,
                status TEXT,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (query_id) REFERENCES shared_queries (id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_project(self, project: Project) -> int:
        """Create new project"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        team_members_json = json.dumps(project.team_members or [])
        
        cursor.execute("""
            INSERT INTO projects (name, description, owner_id, team_members, status)
            VALUES (?, ?, ?, ?, ?)
        """, (project.name, project.description, project.owner_id, team_members_json, project.status))
        
        project_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return project_id
    
    def get_user_projects(self, user_id: int) -> List[Project]:
        """Get projects for user (owned or member)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, description, owner_id, team_members, status, created_at
            FROM projects 
            WHERE owner_id = ? OR team_members LIKE ?
            ORDER BY created_at DESC
        """, (user_id, f'%{user_id}%'))
        
        rows = cursor.fetchall()
        conn.close()
        
        projects = []
        for row in rows:
            team_members = json.loads(row[4] or '[]')
            projects.append(Project(
                id=row[0],
                name=row[1],
                description=row[2],
                owner_id=row[3],
                team_members=team_members,
                status=row[5],
                created_at=row[6]
            ))
        
        return projects
    
    def share_query(self, query: SharedQuery) -> int:
        """Share a query with team"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tags_json = json.dumps(query.tags or [])
        
        cursor.execute("""
            INSERT INTO shared_queries 
            (title, sql_query, description, project_id, created_by, tags, is_public)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (query.title, query.sql_query, query.description, 
              query.project_id, query.created_by, tags_json, query.is_public))
        
        query_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return query_id
    
    def get_shared_queries(self, user_id: int, project_id: Optional[int] = None) -> List[SharedQuery]:
        """Get shared queries for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if project_id:
            cursor.execute("""
                SELECT id, title, sql_query, description, project_id, created_by, 
                       tags, is_public, execution_count, created_at
                FROM shared_queries 
                WHERE project_id = ? OR (is_public = 1 AND created_by = ?)
                ORDER BY created_at DESC
            """, (project_id, user_id))
        else:
            cursor.execute("""
                SELECT id, title, sql_query, description, project_id, created_by, 
                       tags, is_public, execution_count, created_at
                FROM shared_queries 
                WHERE created_by = ? OR is_public = 1
                ORDER BY created_at DESC
            """, (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        queries = []
        for row in rows:
            tags = json.loads(row[6] or '[]')
            queries.append(SharedQuery(
                id=row[0],
                title=row[1],
                sql_query=row[2],
                description=row[3],
                project_id=row[4],
                created_by=row[5],
                tags=tags,
                is_public=bool(row[7]),
                execution_count=row[8],
                created_at=row[9]
            ))
        
        return queries
    
    def add_comment(self, comment: Comment) -> int:
        """Add comment to query"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO comments (content, query_id, user_id, username)
            VALUES (?, ?, ?, ?)
        """, (comment.content, comment.query_id, comment.user_id, comment.username))
        
        comment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return comment_id
    
    def get_query_comments(self, query_id: int) -> List[Comment]:
        """Get comments for query"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, content, query_id, user_id, username, created_at
            FROM comments 
            WHERE query_id = ?
            ORDER BY created_at ASC
        """, (query_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [Comment(
            id=row[0],
            content=row[1],
            query_id=row[2],
            user_id=row[3],
            username=row[4],
            created_at=row[5]
        ) for row in rows]
    
    def record_query_execution(self, query_id: int, user_id: int, 
                             execution_time: float, result_rows: int, status: str):
        """Record query execution for analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Record execution
        cursor.execute("""
            INSERT INTO query_executions 
            (query_id, user_id, execution_time, result_rows, status)
            VALUES (?, ?, ?, ?, ?)
        """, (query_id, user_id, execution_time, result_rows, status))
        
        # Update execution count
        cursor.execute("""
            UPDATE shared_queries 
            SET execution_count = execution_count + 1 
            WHERE id = ?
        """, (query_id,))
        
        conn.commit()
        conn.close()
    
    def get_team_analytics(self, project_id: Optional[int] = None) -> Dict:
        """Get team collaboration analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        analytics = {}
        
        # Query usage stats
        if project_id:
            cursor.execute("""
                SELECT COUNT(*), AVG(execution_count), SUM(execution_count)
                FROM shared_queries WHERE project_id = ?
            """, (project_id,))
        else:
            cursor.execute("""
                SELECT COUNT(*), AVG(execution_count), SUM(execution_count)
                FROM shared_queries
            """)
        
        row = cursor.fetchone()
        analytics['total_queries'] = row[0]
        analytics['avg_executions'] = round(row[1] or 0, 2)
        analytics['total_executions'] = row[2] or 0
        
        # Most active users
        cursor.execute("""
            SELECT u.username, COUNT(*) as queries_created
            FROM shared_queries sq
            JOIN users u ON sq.created_by = u.id
            GROUP BY u.username
            ORDER BY queries_created DESC
            LIMIT 5
        """)
        
        analytics['top_contributors'] = [
            {'username': row[0], 'queries': row[1]} 
            for row in cursor.fetchall()
        ]
        
        # Recent activity
        cursor.execute("""
            SELECT title, created_at, execution_count
            FROM shared_queries
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        analytics['recent_activity'] = [
            {'title': row[0], 'created': row[1], 'executions': row[2]}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return analytics

def render_team_collaboration_ui():
    """Render team collaboration interface"""
    st.title("Team Collaboration Hub")
    
    # Initialize collaboration system
    if 'collaboration' not in st.session_state:
        st.session_state.collaboration = TeamCollaboration()
    
    # Mock current user for demo (in production, get from auth)
    current_user = User(id=1, username="demo_user", email="demo@test.com", role="user")
    
    # Main navigation
    tab1, tab2, tab3, tab4 = st.tabs(["Projects", "Shared Queries", "Team Analytics", "My Contributions"])
    
    with tab1:
        st.subheader("Team Projects")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Create new project
            with st.expander("Create New Project"):
                project_name = st.text_input("Project Name")
                project_desc = st.text_area("Description")
                if st.button("Create Project"):
                    if project_name:
                        project = Project(
                            name=project_name,
                            description=project_desc,
                            owner_id=current_user.id,
                            team_members=[current_user.id]
                        )
                        project_id = st.session_state.collaboration.create_project(project)
                        st.success(f"Project '{project_name}' created!")
                        st.rerun()
        
        with col2:
            st.metric("My Projects", "3")
            st.metric("Team Members", "8")
        
        # Display projects
        projects = st.session_state.collaboration.get_user_projects(current_user.id)
        
        for project in projects[:3]:  # Show first 3 projects
            with st.container():
                st.markdown(f"### {project.name}")
                st.write(project.description)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"Owner: User {project.owner_id}")
                with col2:
                    st.write(f"Members: {len(project.team_members or [])}")
                with col3:
                    st.write(f"Status: {project.status}")
                
                st.divider()
    
    with tab2:
        st.subheader("Shared SQL Queries")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Share new query
            with st.expander("Share New Query"):
                query_title = st.text_input("Query Title")
                query_sql = st.text_area("SQL Query", height=100)
                query_desc = st.text_area("Description")
                query_tags = st.text_input("Tags (comma separated)")
                is_public = st.checkbox("Make Public")
                
                if st.button("Share Query"):
                    if query_title and query_sql:
                        shared_query = SharedQuery(
                            title=query_title,
                            sql_query=query_sql,
                            description=query_desc,
                            created_by=current_user.id,
                            tags=query_tags.split(',') if query_tags else [],
                            is_public=is_public
                        )
                        query_id = st.session_state.collaboration.share_query(shared_query)
                        st.success("Query shared successfully!")
                        st.rerun()
        
        with col2:
            st.metric("Shared Queries", "12")
            st.metric("My Queries", "5")
        
        # Display shared queries
        queries = st.session_state.collaboration.get_shared_queries(current_user.id)
        
        for query in queries[:5]:  # Show first 5 queries
            with st.container():
                st.markdown(f"**{query.title}**")
                st.write(query.description)
                
                # Query preview
                st.code(query.sql_query[:200] + "..." if len(query.sql_query) > 200 else query.sql_query, 
                       language="sql")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(f"Executions: {query.execution_count}")
                with col2:
                    st.write(f"Public: {'Yes' if query.is_public else 'No'}")
                with col3:
                    if st.button(f"Execute", key=f"exec_{query.id}"):
                        st.info("Query executed! (Demo mode)")
                with col4:
                    if st.button(f"Comment", key=f"comment_{query.id}"):
                        st.session_state[f'show_comments_{query.id}'] = True
                
                # Comments section
                if st.session_state.get(f'show_comments_{query.id}', False):
                    st.markdown("**Comments:**")
                    
                    # Add comment
                    new_comment = st.text_input(f"Add comment", key=f"new_comment_{query.id}")
                    if st.button(f"Post", key=f"post_{query.id}") and new_comment:
                        comment = Comment(
                            content=new_comment,
                            query_id=query.id,
                            user_id=current_user.id,
                            username=current_user.username
                        )
                        st.session_state.collaboration.add_comment(comment)
                        st.success("Comment added!")
                        st.rerun()
                    
                    # Show existing comments
                    comments = st.session_state.collaboration.get_query_comments(query.id)
                    for comment in comments:
                        st.write(f"**{comment.username}**: {comment.content}")
                        st.caption(f"Posted: {comment.created_at}")
                
                st.divider()
    
    with tab3:
        st.subheader("Team Analytics")
        
        analytics = st.session_state.collaboration.get_team_analytics()
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Queries", analytics['total_queries'])
        with col2:
            st.metric("Total Executions", analytics['total_executions'])
        with col3:
            st.metric("Avg Executions", analytics['avg_executions'])
        with col4:
            st.metric("Active Contributors", len(analytics['top_contributors']))
        
        # Top contributors chart
        if analytics['top_contributors']:
            st.subheader("Top Contributors")
            contrib_df = pd.DataFrame(analytics['top_contributors'])
            st.bar_chart(contrib_df.set_index('username')['queries'])
        
        # Recent activity
        st.subheader("Recent Activity")
        if analytics['recent_activity']:
            activity_df = pd.DataFrame(analytics['recent_activity'])
            st.dataframe(activity_df, use_container_width=True)
    
    with tab4:
        st.subheader("My Contributions")
        
        # User's shared queries
        user_queries = [q for q in queries if q.created_by == current_user.id]
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Queries Shared", len(user_queries))
        with col2:
            total_executions = sum(q.execution_count for q in user_queries)
            st.metric("Total Executions", total_executions)
        
        # Query performance
        if user_queries:
            st.subheader("Query Performance")
            query_data = [
                {'Title': q.title, 'Executions': q.execution_count, 'Public': q.is_public}
                for q in user_queries
            ]
            df = pd.DataFrame(query_data)
            st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    render_team_collaboration_ui()