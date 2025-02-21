import jwt
import datetime
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymongo import MongoClient
from dotenv import load_dotenv
import os


# Configurações de segurança
load_dotenv()
SECRET_KEY = "SECRET_KEY"
ALGORITHM = "HS256"
security = HTTPBearer()

# Conexão com o MongoDB

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["users-api"]

# Funções JWT
def criar_token(data: dict):
    """
    Gera um token JWT.
    """
    payload = {
        **data,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verificar_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verifica se o token JWT é válido.
    """
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

# Função de autenticação
def autenticar_usuario(username: str, password: str):
    """
    Autentica o usuário no banco de dados.
    """
    usuario = db["usuarios"].find_one({"username": username})
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    if usuario["password"] != password:
        raise HTTPException(status_code=401, detail="Senha incorreta")
    if usuario.get("status") != "ATIVO":
        raise HTTPException(status_code=401, detail="Usuário inativo")
    return criar_token({"user_id": usuario["_id"],"tipo": "basic"})

