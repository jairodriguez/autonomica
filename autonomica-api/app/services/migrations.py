import pandas as pd
from sqlalchemy.orm import Session
from app.models import Task, Agent, ContentPiece, SocialPost
from .database import engine

def export_table_to_csv(session: Session, model, file_path):
    query = session.query(model)
    df = pd.read_sql(query.statement, session.bind)
    df.to_csv(file_path, index=False)

def import_csv_to_table(file_path, model):
    df = pd.read_csv(file_path)
    df.to_sql(model.__tablename__, con=engine, if_exists='append', index=False)

def export_all_data(session: Session, export_dir='data_export'):
    import os
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
        
    export_table_to_csv(session, Task, f'{export_dir}/tasks.csv')
    export_table_to_csv(session, Agent, f'{export_dir}/agents.csv')
    export_table_to_csv(session, ContentPiece, f'{export_dir}/content_pieces.csv')
    export_table_to_csv(session, SocialPost, f'{export_dir}/social_posts.csv')

def import_all_data(import_dir='data_export'):
    import_csv_to_table(f'{import_dir}/tasks.csv', Task)
    import_csv_to_table(f'{import_dir}/agents.csv', Agent)
    import_csv_to_table(f'{import_dir}/content_pieces.csv', ContentPiece)
    import_csv_to_table(f'{import_dir}/social_posts.csv', SocialPost) 