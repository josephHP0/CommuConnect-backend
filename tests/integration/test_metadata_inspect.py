import os
import sys

#Asegúrate de que "app" esté en sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sqlmodel import SQLModel
from app.modules.services.models import Local  # El modelo que incluye la tabla 'local'
from app.core.db import engine  # Donde defines tu engine

print("Columnas registradas en la tabla 'local':")
local_table = SQLModel.metadata.tables["local"]
for column in local_table.columns:
    print(f"🔸 {column.name} ({column.type})")
