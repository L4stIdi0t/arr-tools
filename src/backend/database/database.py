import os
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.media import Base as media_base
from models.webSettings import Base as web_base

# region Configuration and Setup

# Load environment variables from .env file
load_dotenv()

# Get database URLs from environment variables
DATABASE_URL_PROGRAM = "sqlite:///data/database.db"

# Ensure the directory exists
os.makedirs(os.path.dirname(os.path.abspath("data/database.db")), exist_ok=True)

# Create engines for user and program data
program_data_engine = create_engine(DATABASE_URL_PROGRAM)

# Create tables if they do not exist
media_base.metadata.create_all(program_data_engine)
web_base.metadata.create_all(program_data_engine)

# Create session makers for user and program data
ProgramSessionLocal = sessionmaker(
    autocommit=False, autoflush=True, bind=program_data_engine
)

# endregion


# region Dependency Injection
def get_program_db():
    db = ProgramSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dependencies annotated with types for FastAPI
program_db_dependency = Annotated[ProgramSessionLocal, Depends(get_program_db)]

# endregion
