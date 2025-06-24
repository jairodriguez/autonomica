from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, selectinload
from app.models import Base, Task, Agent, ContentPiece, SocialPost, AgentContext, User
import os
from typing import Type

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./autonomica.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

task_cache = {}
agent_cache = {}

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_or_create_agent(db: Session, name: str, role: str, capabilities: dict) -> Agent:
    agent = db.query(Agent).filter(Agent.name == name).first()
    if not agent:
        agent = Agent(name=name, role=role, capabilities=capabilities)
        db.add(agent)
        db.commit()
        db.refresh(agent)
    return agent

def create_task(db: Session, title: str, description: str, agent_id: int) -> Task:
    task = Task(title=title, description=description, agent_id=agent_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def create_content_piece(db: Session, title: str, content: str, type: str) -> ContentPiece:
    content_piece = ContentPiece(title=title, content=content, type=type)
    db.add(content_piece)
    db.commit()
    db.refresh(content_piece)
    return content_piece

def create_social_post(db: Session, platform: str, content_id: int, metrics: dict) -> SocialPost:
    social_post = SocialPost(platform=platform, content_id=content_id, metrics=metrics)
    db.add(social_post)
    db.commit()
    db.refresh(social_post)
    return social_post

def create_agent_context(db: Session, agent_id: int, context: dict) -> AgentContext:
    agent_context = AgentContext(agent_id=agent_id, context=context)
    db.add(agent_context)
    db.commit()
    db.refresh(agent_context)
    return agent_context

def get_agent_context(db: Session, agent_id: int) -> AgentContext:
    return db.query(AgentContext).filter(AgentContext.agent_id == agent_id).first()

def get_or_create_user(db: Session, clerk_id: str) -> User:
    user = db.query(User).filter(User.clerk_id == clerk_id).first()
    if not user:
        user = User(clerk_id=clerk_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def get_user_by_clerk_id(db: Session, clerk_id: str) -> User:
    return db.query(User).filter(User.clerk_id == clerk_id).first()

def get_task(db: Session, task_id: int) -> Task:
    return db.query(Task).filter(Task.id == task_id).first()

def get_tasks(db: Session, skip: int = 0, limit: int = 100):
    if 'all' in task_cache:
        return task_cache['all'][skip:skip+limit]
    
    tasks = db.query(Task).options(selectinload(Task.agent)).offset(skip).limit(limit).all()
    task_cache['all'] = tasks
    return tasks

def get_agent(db: Session, agent_id: int) -> Agent:
    return db.query(Agent).filter(Agent.id == agent_id).first()

def get_agents(db: Session, skip: int = 0, limit: int = 100):
    if 'all' in agent_cache:
        return agent_cache['all'][skip:skip+limit]

    agents = db.query(Agent).options(selectinload(Agent.tasks)).offset(skip).limit(limit).all()
    agent_cache['all'] = agents
    return agents

def get_content_piece(db: Session, content_id: int) -> ContentPiece:
    return db.query(ContentPiece).filter(ContentPiece.id == content_id).first()

def get_social_post(db: Session, post_id: int) -> SocialPost:
    return db.query(SocialPost).filter(SocialPost.id == post_id).first()

def check_orphaned_tasks(db: Session):
    tasks = db.query(Task).all()
    orphaned_tasks = []
    for task in tasks:
        if not task.agent:
            orphaned_tasks.append(task)
    return orphaned_tasks 