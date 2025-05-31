from sqlmodel import SQLModel, Session, create_engine
import os
from dotenv import load_dotenv
from pathlib import Path

# Cargar el archivo .env desde la raíz del proyecto
dotenv_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path)


DATABASE_URL = os.getenv("DATABASE_URL")

print(f"DATABASE_URL cargada: {DATABASE_URL}")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no se encontró en el archivo .env")

engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session


