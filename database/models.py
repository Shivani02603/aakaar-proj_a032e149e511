import os
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    UUID,
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session as DBSession
from sqlalchemy.sql import func

# Use environment variable for database URL
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/rag_app")

# Create engine and session factory
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = UUID(primary_key=True, default=uuid4)
    email = String(255, nullable=False, unique=True)
    api_key = String(255, nullable=False, unique=True)

    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class Session(Base):
    __tablename__ = "sessions"

    id = UUID(primary_key=True, default=uuid4)
    user_id = UUID(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = String(255, nullable=False)
    created_at = DateTime(server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")
    uploaded_files = relationship("UploadedFile", back_populates="session", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_sessions_user_id", "user_id"),
        Index("ix_sessions_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<Session(id={self.id}, name={self.name}, user_id={self.user_id})>"


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = UUID(primary_key=True, default=uuid4)
    session_id = UUID(ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    filename = String(255, nullable=False)
    file_size_bytes = BigInteger(nullable=False)
    uploaded_at = DateTime(server_default=func.now(), nullable=False)

    # Relationships
    session = relationship("Session", back_populates="uploaded_files")
    chunks = relationship("Chunk", back_populates="uploaded_file", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_uploaded_files_session_id", "session_id"),
        Index("ix_uploaded_files_uploaded_at", "uploaded_at"),
    )

    def __repr__(self):
        return f"<UploadedFile(id={self.id}, filename={self.filename}, session_id={self.session_id})>"


class Chunk(Base):
    __tablename__ = "chunks"

    id = UUID(primary_key=True, default=uuid4)
    uploaded_file_id = UUID(ForeignKey("uploaded_files.id", ondelete="CASCADE"), nullable=False)
    content = Text(nullable=False)
    embedding = None  # Will be defined as a custom column for pgvector
    sheet_name = String(255, nullable=False)
    row_start = Integer(nullable=False)
    row_end = Integer(nullable=False)
    chunk_index = Integer(nullable=False)

    # Relationships
    uploaded_file = relationship("UploadedFile", back_populates="chunks")

    # Indexes
    __table_args__ = (
        Index("ix_chunks_uploaded_file_id", "uploaded_file_id"),
        Index("ix_chunks_sheet_name", "sheet_name"),
        Index("ix_chunks_row_start", "row_start"),
        Index("ix_chunks_row_end", "row_end"),
        Index("ix_chunks_chunk_index", "chunk_index"),
    )

    def __repr__(self):
        return f"<Chunk(id={self.id}, sheet={self.sheet_name}, rows={self.row_start}-{self.row_end}, index={self.chunk_index})>"


class Message(Base):
    __tablename__ = "messages"

    id = UUID(primary_key=True, default=uuid4)
    session_id = UUID(ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    role = String(50, nullable=False)  # 'user' or 'assistant'
    content = Text(nullable=False)
    citations = JSONB(nullable=True)  # Store source citations as JSON
    created_at = DateTime(server_default=func.now(), nullable=False)

    # Relationships
    session = relationship("Session", back_populates="messages")

    # Indexes
    __table_args__ = (
        Index("ix_messages_session_id", "session_id"),
        Index("ix_messages_created_at", "created_at"),
        Index("ix_messages_role", "role"),
    )

    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, session_id={self.session_id})>"


# Function to add pgvector support after table creation
def setup_pgvector():
    """Create the vector extension and add the embedding column to Chunk table."""
    with engine.connect() as conn:
        # Enable pgvector extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    # Now we need to alter the Chunk table to add the embedding column
    # Since SQLAlchemy doesn't have built-in support for pgvector,
    # we'll handle this via raw SQL
    with engine.connect() as conn:
        # Check if embedding column already exists
        result = conn.execute(
            text(
                """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='chunks' AND column_name='embedding'
            """
            )
        ).fetchone()

        if not result:
            # Add embedding column with vector type (1536 dimensions for text-embedding-3-small)
            conn.execute(text("ALTER TABLE chunks ADD COLUMN embedding vector(1536)"))
            # Create index for vector similarity search
            conn.execute(text("CREATE INDEX ix_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops)"))
            conn.commit()


# Create all tables
Base.metadata.create_all(bind=engine)

# Setup pgvector extension and column
setup_pgvector()