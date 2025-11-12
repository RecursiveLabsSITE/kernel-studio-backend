```python
"""
Storage module — PostgreSQL-backed storage
Handles all data persistence for kernels
"""

import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional
import time


class Store:
    """PostgreSQL-backed storage for kernel data"""
    
    def init(self, data_root: str = "./storage"):
        """Initialize PostgreSQL connection (data_root ignored for compatibility)"""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        self.conn = psycopg2.connect(database_url)
        self.conn.autocommit = True
        self._init_tables()
    
    def _init_tables(self):
        """Create tables if they don't exist"""
        with self.conn.cursor() as cur:
            # Kernels table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS kernels (
                    kernel_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    bio TEXT,
                    era TEXT,
                    created_at BIGINT
                )
            """)
            
            # Deep memories table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS deep_memories (
                    id SERIAL PRIMARY KEY,
                    kernel_id TEXT NOT NULL,
                    chunk_data JSONB NOT NULL,
                    created_at BIGINT,
                    FOREIGN KEY (kernel_id) REFERENCES kernels(kernel_id) ON DELETE CASCADE
                )
            """)
            
            # Contradictions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS contradictions (
                    id SERIAL PRIMARY KEY,
                    kernel_id TEXT NOT NULL,
                    contradiction_data JSONB NOT NULL,
                    created_at BIGINT,
                    FOREIGN KEY (kernel_id) REFERENCES kernels(kernel_id) ON DELETE CASCADE
                )
            """)
    
    def save_meta(self, kernel_id: str, meta: dict):
        """Save kernel metadata"""
        created_at = meta.get("created_at") or int(time.time())
        
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO kernels (kernel_id, name, bio, era, created_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (kernel_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    bio = EXCLUDED.bio,
                    era = EXCLUDED.era
            """, (
                kernel_id,
                meta.get("name", ""),
                meta.get("bio", ""),
                meta.get("era", ""),
                created_at
            ))
    
    def get_meta(self, kernel_id: str) -> Optional[dict]:
        """Get kernel metadata"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT kernel_id, name, bio, era, created_at
                FROM kernels
                WHERE kernel_id = %s
            """, (kernel_id,))
            result = cur.fetchone()
            return dict(result) if result else None
    
    def list_kernels(self) -> List[dict]:
        """List all kernels"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT kernel_id, name, bio, era, created_at
                FROM kernels
                ORDER BY created_at DESC
            """)
            results = cur.fetchall()
            return [dict(row) for row in results]
    
    def delete_kernel(self, kernel_id: str) -> bool:
        """Delete a kernel and all its data"""
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM kernels WHERE kernel_id = %s", (kernel_id,))
            return cur.rowcount > 0
    
    def add_deep(self, kernel_id: str, chunks: List[dict]):
        """Add deep memory chunks"""
        with self.conn.cursor() as cur:
            for chunk in chunks:
                cur.execute("""
                    INSERT INTO deep_memories (kernel_id, chunk_data, created_at)
                    VALUES (%s, %s, %s)
                """, (
                    kernel_id,
                    json.dumps(chunk),
                    int(time.time())
                ))
    
    def get_deep(self, kernel_id: str) -> List[dict]:
        """Get all deep memories"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT chunk_data
                FROM deep_memories
                WHERE kernel_id = %s
                ORDER BY created_at ASC
            """, (kernel_id,))
            results = cur.fetchall()
            return [json.loads(row['chunk_data']) for row in results]
    
    def add_contradictions(self, kernel_id: str, contradictions: List[dict]):
        """Add contradictions"""
        with self.conn.cursor() as cur:
            for contradiction in contradictions:
                cur.execute("""
                    INSERT INTO contradictions (kernel_id, contradiction_data, created_at)
                    VALUES (%s, %s, %s)
                """, (
                    kernel_id,
                    json.dumps(contradiction),
                    int(time.time())
                ))
    
    def get_contradictions(self, kernel_id: str) -> List[dict]:
        """Get all contradictions"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT contradiction_data
                FROM contradictions
                WHERE kernel_id = %s
                ORDER BY created_at ASC
            """, (kernel_id,))
            results = cur.fetchall()
            return [json.loads(row['contradiction_data']) for row in results]
