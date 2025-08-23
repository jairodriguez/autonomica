from sqlalchemy import (
    Column, 
    Integer, 
    String, 
    Float, 
    DateTime, 
    JSON, 
    ForeignKey,
    Text,
    Enum as PyEnum,
    Boolean
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

class UserRole(enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EDITOR = "editor"
    CREATOR = "creator"
    VIEWER = "viewer"

class Permission(enum.Enum):
    # Content Management
    CREATE_CONTENT = "create_content"
    EDIT_CONTENT = "edit_content"
    DELETE_CONTENT = "delete_content"
    PUBLISH_CONTENT = "publish_content"
    APPROVE_CONTENT = "approve_content"
    
    # Social Media Management
    MANAGE_SOCIAL_ACCOUNTS = "manage_social_accounts"
    SCHEDULE_POSTS = "schedule_posts"
    PUBLISH_POSTS = "publish_posts"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_ANALYTICS = "manage_analytics"
    
    # User Management
    MANAGE_USERS = "manage_users"
    ASSIGN_ROLES = "assign_roles"
    VIEW_USERS = "view_users"
    
    # System Management
    MANAGE_SETTINGS = "manage_settings"
    VIEW_LOGS = "view_logs"
    MANAGE_INTEGRATIONS = "manage_integrations"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    clerk_id = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    role = Column(PyEnum(UserRole), default=UserRole.CREATOR)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tasks = relationship("Task", back_populates="user")
    agents = relationship("Agent", back_populates="user")
    user_permissions = relationship("UserPermission", back_populates="user")
    social_accounts = relationship("SocialAccount", back_populates="user")
    content_pieces = relationship("ContentPiece", back_populates="user")
    social_posts = relationship("SocialPost", back_populates="user")

class UserPermission(Base):
    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    permission = Column(PyEnum(Permission), nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow)
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    expires_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="user_permissions", foreign_keys=[user_id])
    granted_by_user = relationship("User", foreign_keys=[granted_by])

class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    platform = Column(String, nullable=False)  # twitter, facebook, linkedin, instagram
    account_name = Column(String, nullable=False)
    account_id = Column(String, nullable=False)  # Platform-specific account ID
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    permissions = Column(JSON)  # Platform-specific permissions
    platform_metadata = Column(JSON)  # Additional platform data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="social_accounts")

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
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="content_pieces")
    social_posts = relationship("SocialPost", back_populates="content_piece")

class SocialPost(Base):
    __tablename__ = "social_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String, nullable=False) # e.g., 'twitter', 'linkedin'
    content_id = Column(Integer, ForeignKey("content_pieces.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    status = Column(PyEnum(ContentStatus), default=ContentStatus.DRAFT)
    metrics = Column(JSON) # e.g., likes, shares, comments
    publish_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    content_piece = relationship("ContentPiece", back_populates="social_posts")
    user = relationship("User", back_populates="social_posts") 