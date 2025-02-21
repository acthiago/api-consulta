from passlib.context import CryptContext
from jose import jwt 
import datetime
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from pymongo import MongoClient

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["users-api"]

def autenticar_usuario(username: str, password: str):
    """
    Verifica se o usuário e senha são válidos.
    """
    usuario = db["usuarios"].find_one({"username": username})
    if not usuario or not pwd_context.verify(password, usuario["password"]):
        return None
    return criar_token({"sub": username})

def criar_token(data: dict):
    """
    Gera um token JWT.
    """
    expire = datetime.utcnow() + timedelta(hours=2)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
