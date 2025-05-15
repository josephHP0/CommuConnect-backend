from pathlib import Path
from dotenv import load_dotenv
import os
from sqlmodel import SQLModel, Session, create_engine

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(dotenv_path=BASE_DIR / ".env")

print("BASE_DIR:", BASE_DIR)
print("DATABASE_URL leído:", os.getenv("DATABASE_URL"))


DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    """Crea tablas según los modelos declarados."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """
    Provee un generator de sesión de base de datos.
    """
    with Session(engine) as session:
        yield session