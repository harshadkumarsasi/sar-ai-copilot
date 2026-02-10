

"""
PostgreSQL helper module for SAR AI Copilot.

Responsibilities:
- Create and manage DB connections
- Initialize core tables (cases, audit_logs)
- Provide simple insert/query helpers for the rest of the app

This file is intentionally lightweight and hackathon-safe.
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

DATABASE_URL = os.getenv("POSTGRES_URL")


class PostgresClient:
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or DATABASE_URL
        if not self.db_url:
            raise ValueError("POSTGRES_URL is not set in environment variables")

    def connect(self):
        return psycopg2.connect(
            self.db_url,
            cursor_factory=RealDictCursor,
        )

    def init_tables(self):
        """Create required tables if they do not exist."""
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS cases (
                        id SERIAL PRIMARY KEY,
                        customer_id TEXT,
                        risk_score FLOAT,
                        status TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )

                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS audit_logs (
                        id SERIAL PRIMARY KEY,
                        case_id INTEGER,
                        action TEXT,
                        details JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )
            conn.commit()

    def create_case(self, customer_id: str, risk_score: float, status: str = "draft") -> int:
        """Insert a new SAR case and return its ID."""
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO cases (customer_id, risk_score, status)
                    VALUES (%s, %s, %s)
                    RETURNING id;
                    """,
                    (customer_id, risk_score, status),
                )
                case_id = cur.fetchone()["id"]
            conn.commit()
        return case_id

    def log_action(self, case_id: int, action: str, details: Dict[str, Any]):
        """Insert an audit log entry."""
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO audit_logs (case_id, action, details)
                    VALUES (%s, %s, %s);
                    """,
                    (case_id, action, details),
                )
            conn.commit()