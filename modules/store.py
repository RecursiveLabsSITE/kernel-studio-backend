"""
Kernel Studio v1.1 - PostgreSQL Store for Supabase
Replaces in-memory storage with persistent Supabase Postgres.
"""

import os
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from contextlib import contextmanager


class SupabaseStore:
    """PostgreSQL-backed store connecting to Supabase."""
    
    def __init__(self):
        # Build connection string from Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL", "")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        
        # Extract project ID from URL (e.g., keobizfexzzivtdwrixc)
        project_id = supabase_url.split("//")[1].split(".")[0] if supabase_url else ""
        
        # Supabase Postgres connection string format
        self.conn_str = (
            f"postgresql://postgres.{project_id}:{supabase_key}@"
            f"aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        )
        
        print(f"[Store] Initializing Supabase Postgres store for project: {project_id}")
        self._test_connection()
    
    @contextmanager
    def get_conn(self):
        """Context manager for database connections."""
        conn = psycopg2.connect(self.conn_str)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _test_connection(self):
        """Test database connection on startup."""
        try:
            with self.get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    print("[Store] ✅ Database connection successful")
        except Exception as e:
            print(f"[Store] ❌ Database connection failed: {e}")
            raise
    
    # ========== KERNELS ==========
    
    def get_kernel(self, kernel_id: str) -> Optional[Dict[str, Any]]:
        """Get kernel by ID."""
        with self.get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM kernels WHERE id = %s",
                    (kernel_id,)
                )
                row = cur.fetchone()
                return dict(row) if row else None
    
    def update_kernel_status(self, kernel_id: str, status: str, stats: Optional[Dict] = None):
        """Update kernel status and stats."""
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                if stats:
                    cur.execute(
                        """UPDATE kernels 
                           SET status = %s, stats = %s, last_built_at = NOW()
                           WHERE id = %s""",
                        (status, Json(stats), kernel_id)
                    )
                else:
                    cur.execute(
                        "UPDATE kernels SET status = %s WHERE id = %s",
                        (status, kernel_id)
                    )
    
    def get_kernel_settings(self, kernel_id: str) -> Dict[str, Any]:
        """Get kernel settings (models, weights, safety)."""
        with self.get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM kernel_settings WHERE kernel_id = %s",
                    (kernel_id,)
                )
                row = cur.fetchone()
                if row:
                    return dict(row)
                else:
                    # Return defaults if not set
                    return {
                        "models": {"embed": "bge-m3", "llm": "gpt-4"},
                        "weights": {
                            "pair": 0.32,
                            "single": 0.12,
                            "cluster": 0.16,
                            "scar_phase": 0.14,
                            "bias": 0.10,
                            "refusal": 0.10,
                            "mask": 0.06
                        },
                        "safety": {"clear_strictness": 0.8}
                    }
    
    # ========== SOURCES ==========
    
    def create_source(self, kernel_id: str, batch_id: str, storage_path: str, 
                     content_type: str, meta: Dict = None) -> str:
        """Create a new source document."""
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO sources (kernel_id, batch_id, storage_path, content_type, meta)
                       VALUES (%s, %s, %s, %s, %s)
                       RETURNING id""",
                    (kernel_id, batch_id, storage_path, content_type, Json(meta or {}))
                )
                return cur.fetchone()[0]
    
    def get_sources(self, kernel_id: str) -> List[Dict[str, Any]]:
        """Get all sources for a kernel."""
        with self.get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM sources WHERE kernel_id = %s ORDER BY created_at DESC",
                    (kernel_id,)
                )
                return [dict(row) for row in cur.fetchall()]
    
    def update_source_status(self, source_id: str, status: str):
        """Update source parse status."""
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE sources SET parse_status = %s WHERE id = %s",
                    (status, source_id)
                )
    
    # ========== INGEST BATCHES ==========
    
    def create_batch(self, kernel_id: str) -> str:
        """Create a new ingest batch."""
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO ingest_batches (kernel_id, status)
                       VALUES (%s, 'queued')
                       RETURNING id""",
                    (kernel_id,)
                )
                return cur.fetchone()[0]
    
    def update_batch(self, batch_id: str, status: str, step: Dict = None):
        """Update batch status and progress."""
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                if step:
                    cur.execute(
                        "UPDATE ingest_batches SET status = %s, step = %s WHERE id = %s",
                        (status, Json(step), batch_id)
                    )
                else:
                    cur.execute(
                        "UPDATE ingest_batches SET status = %s WHERE id = %s",
                        (status, batch_id)
                    )
    
    def get_batch(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get batch by ID."""
        with self.get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM ingest_batches WHERE id = %s", (batch_id,))
                row = cur.fetchone()
                return dict(row) if row else None
    
    # ========== CONTRADICTIONS ==========
    
    def save_contradiction(self, kernel_id: str, data: Dict[str, Any]) -> str:
        """Save a contradiction."""
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO contradictions (
                        kernel_id, pole_a, pole_b, collapse_direction, scar_valence,
                        refusal, life_phase, life_phase_weight, event, quote_ref,
                        cluster_id, mask_inner, mask_outer, mask_polarity, 
                        mask_loop_hint, mask_signals, summary, embedding
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING id""",
                    (
                        kernel_id,
                        data.get('pole_a'),
                        data.get('pole_b'),
                        data.get('collapse_direction'),
                        data.get('scar_valence'),
                        data.get('refusal', False),
                        data.get('life_phase'),
                        data.get('life_phase_weight'),
                        data.get('event'),
                        data.get('quote_ref', []),
                        data.get('cluster_id'),
                        data.get('mask_inner'),
                        data.get('mask_outer'),
                        data.get('mask_polarity'),
                        data.get('mask_loop_hint'),
                        data.get('mask_signals', []),
                        data.get('summary'),
                        data.get('embedding')  # pgvector array
                    )
                )
                return cur.fetchone()[0]
    
    def get_contradictions(self, kernel_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        """Get contradictions for a kernel."""
        with self.get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """SELECT id, pole_a, pole_b, collapse_direction, scar_valence,
                              refusal, life_phase, life_phase_weight, event, summary
                       FROM contradictions 
                       WHERE kernel_id = %s 
                       ORDER BY scar_valence DESC NULLS LAST
                       LIMIT %s""",
                    (kernel_id, limit)
                )
                return [dict(row) for row in cur.fetchall()]
    
    def search_contradictions(self, kernel_id: str, query_embedding: List[float], 
                             limit: int = 10) -> List[Dict[str, Any]]:
        """Vector similarity search for contradictions."""
        with self.get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Convert Python list to PostgreSQL vector format
                embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
                cur.execute(
                    """SELECT id, pole_a, pole_b, collapse_direction, scar_valence,
                              life_phase, summary,
                              embedding <-> %s::vector AS distance
                       FROM contradictions
                       WHERE kernel_id = %s AND embedding IS NOT NULL
                       ORDER BY embedding <-> %s::vector
                       LIMIT %s""",
                    (embedding_str, kernel_id, embedding_str, limit)
                )
                return [dict(row) for row in cur.fetchall()]
    
    # ========== DEEP MEMORIES ==========
    
    def save_deep_memory(self, kernel_id: str, data: Dict[str, Any]) -> str:
        """Save a deep memory (single utterance)."""
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO deep_memories (
                        kernel_id, source_label, text, tags, life_phase, embedding
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id""",
                    (
                        kernel_id,
                        data.get('source_label'),
                        data.get('text'),
                        data.get('tags', []),
                        data.get('life_phase'),
                        data.get('embedding')
                    )
                )
                return cur.fetchone()[0]
    
    def search_deep_memories(self, kernel_id: str, query_embedding: List[float],
                            limit: int = 20) -> List[Dict[str, Any]]:
        """Vector search for deep memories."""
        with self.get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
                cur.execute(
                    """SELECT id, text, source_label, tags, life_phase,
                              embedding <-> %s::vector AS distance
                       FROM deep_memories
                       WHERE kernel_id = %s AND embedding IS NOT NULL
                       ORDER BY embedding <-> %s::vector
                       LIMIT %s""",
                    (embedding_str, kernel_id, embedding_str, limit)
                )
                return [dict(row) for row in cur.fetchall()]
    
    # ========== CLUSTERS ==========
    
    def save_cluster(self, kernel_id: str, label_tokens: List[str], 
                    member_ids: List[str], centroid: List[float]) -> str:
        """Save a cluster."""
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                centroid_str = "[" + ",".join(map(str, centroid)) + "]"
                cur.execute(
                    """INSERT INTO clusters (kernel_id, label_tokens, member_ids, centroid)
                       VALUES (%s, %s, %s, %s::vector)
                       RETURNING id""",
                    (kernel_id, label_tokens, member_ids, centroid_str)
                )
                return cur.fetchone()[0]
    
    def get_clusters(self, kernel_id: str) -> List[Dict[str, Any]]:
        """Get all clusters for a kernel."""
        with self.get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, label_tokens, member_ids FROM clusters WHERE kernel_id = %s",
                    (kernel_id,)
                )
                return [dict(row) for row in cur.fetchall()]
    
    # ========== GRAPH EDGES ==========
    
    def save_graph_edge(self, kernel_id: str, pole_a: str, pole_b: str,
                       frequency: int, direction_bias: float, scar_sum: float,
                       refusal_present: bool = False) -> str:
        """Save a graph edge."""
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO graph_edges (
                        kernel_id, pole_a, pole_b, frequency, 
                        direction_bias, scar_sum, refusal_present
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id""",
                    (kernel_id, pole_a, pole_b, frequency, direction_bias, 
                     scar_sum, refusal_present)
                )
                return cur.fetchone()[0]
    
    def get_graph_edges(self, kernel_id: str) -> List[Dict[str, Any]]:
        """Get all graph edges for a kernel."""
        with self.get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """SELECT pole_a, pole_b, frequency, direction_bias, 
                              scar_sum, refusal_present
                       FROM graph_edges 
                       WHERE kernel_id = %s
                       ORDER BY frequency DESC""",
                    (kernel_id,)
                )
                return [dict(row) for row in cur.fetchall()]
    
    # ========== CHAT ==========
    
    def create_thread(self, kernel_id: str, title: str, user_id: str = None) -> str:
        """Create a chat thread."""
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO chat_threads (kernel_id, title, created_by)
                       VALUES (%s, %s, %s)
                       RETURNING id""",
                    (kernel_id, title, user_id)
                )
                return cur.fetchone()[0]
    
    def save_message(self, thread_id: str, role: str, content: str, 
                    trace: Dict = None) -> str:
        """Save a chat message."""
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO chat_messages (thread_id, role, content, trace)
                       VALUES (%s, %s, %s, %s)
                       RETURNING id""",
                    (thread_id, role, content, Json(trace) if trace else None)
                )
                return cur.fetchone()[0]
    
    def get_thread_messages(self, thread_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get messages for a thread."""
        with self.get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """SELECT role, content, trace, created_at
                       FROM chat_messages
                       WHERE thread_id = %s
                       ORDER BY created_at ASC
                       LIMIT %s""",
                    (thread_id, limit)
                )
                return [dict(row) for row in cur.fetchall()]
    
    # ========== PROMPTS ==========
    
    def get_system_prompt(self, kernel_id: str) -> Optional[str]:
        """Get the latest system prompt for a kernel."""
        with self.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT system_text FROM prompts 
                       WHERE kernel_id = %s 
                       ORDER BY created_at DESC 
                       LIMIT 1""",
                    (kernel_id,)
                )
                row = cur.fetchone()
                return row[0] if row else None


# Global store instance
store = SupabaseStore()
