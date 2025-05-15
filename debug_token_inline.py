# debug_token_inline.py
from jose import jwt

SECRET_KEY = "clave_secreta_123"
ALGORITHM  = "HS256"
# Aquí pegas tu JWT puro:
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOnsic3ViIjoiNiJ9LCJpYXQiOjE3NDczNDY4NzgsImV4cCI6MTc0NzM1MDQ3OH0.Z4D6LsEEwWIdRodLnjoiCnMSX_MDlRpSOKghYs7t7QM"

try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    print("✅ Payload decodificado:", payload)
except Exception as e:
    print("❌ Error al decodificar:", e)