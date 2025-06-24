from sqlalchemy import (
    Column, 
    Integer, 
    String, 
    Float, 
    DateTime, 
    JSON, 
    ForeignKey,
    Text,
    Enum as PyEnum
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class TaskStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentStatus(enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"

class ContentStatus(enum.Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    clerk_id = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tasks = relationship("Task", back_populates="user")
    agents = relationship("Agent", back_populates="user")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(PyEnum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(String, default="medium")
    cost_tokens = Column(Integer, default=0)
    agent_id = Column(Integer, ForeignKey("agents.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agent = relationship("Agent", back_populates="tasks")
    user = relationship("User", back_populates="tasks")

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    role = Column(String, nullable=False)
    status = Column(PyEnum(AgentStatus), default=AgentStatus.OFFLINE)
    capabilities = Column(JSON)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tasks = relationship("Task", back_populates="agent")
    contexts = relationship("AgentContext", back_populates="agent")
    user = relationship("User", back_populates="agents")

class AgentContext(Base):
    __tablename__ = "agent_contexts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), index=True)
    context = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agent = relationship("Agent", back_populates="contexts")

class ContentPiece(Base):
    __tablename__ = "content_pieces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String) # e.g., 'blog_post', 'tweet', 'ad_copy'
    status = Column(PyEnum(ContentStatus), default=ContentStatus.DRAFT)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    social_posts = relationship("SocialPost", back_populates="content_piece")

class SocialPost(Base):
    __tablename__ = "social_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String, nullable=False) # e.g., 'twitter', 'linkedin'
    content_id = Column(Integer, ForeignKey("content_pieces.id"), index=True)
    status = Column(PyEnum(ContentStatus), default=ContentStatus.DRAFT)
    metrics = Column(JSON) # e.g., likes, shares, comments
    publish_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    content_piece = relationship("ContentPiece", back_populates="social_posts") 