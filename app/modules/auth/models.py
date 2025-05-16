from sqlmodel import Relationship, SQLModel, Field
from typing import Optional, TYPE_CHECKING
from app.core.enums import TipoUsuario
from sqlalchemy import Column, Enum as SQLEnum
from datetime import datetime

