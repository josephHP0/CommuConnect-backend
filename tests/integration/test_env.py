import os
from dotenv import load_dotenv

load_dotenv()

def test_mostrar_database_url():
    url = os.getenv("DATABASE_URL")
    print("DATABASE_URL cargada:", url)
    assert url is not None and "mysql" in url
