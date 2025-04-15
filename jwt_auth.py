import jwt
import datetime
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import logging

# Configurações de segurança
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")  # Usar um valor padrão apenas para desenvolvimento
ALGORITHM = "HS256"
TOKEN_EXPIRATION_HOURS = int(os.getenv("TOKEN_EXPIRATION_HOURS", 1))  # Configurar expiração via .env
security = HTTPBearer()

# Configuração de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRATION_HOURS)
    }
    logger.info("Token criado para: %s", data)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verificar_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verifica se o token JWT é válido.
    """
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info("Token verificado com sucesso para: %s", payload)
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Tentativa de uso de token expirado.")
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        logger.warning("Tentativa de uso de token inválido.")
        raise HTTPException(status_code=401, detail="Token inválido")

# Função de autenticação
def autenticar_usuario(username: str, password: str):
    """
    Autentica o usuário no banco de dados.
    """
    usuario = db["usuarios"].find_one({"username": username})
    if not usuario:
        logger.warning("Usuário não encontrado: %s", username)
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    if usuario["password"] != password:
        logger.warning("Senha incorreta para o usuário: %s", username)
        raise HTTPException(status_code=401, detail="Senha incorreta")
    if usuario.get("status") != "ATIVO":
        logger.warning("Usuário inativo: %s", username)
        raise HTTPException(status_code=401, detail="Usuário inativo")
    logger.info("Usuário autenticado com sucesso: %s", username)
    return criar_token({"user_id": usuario["_id"], "tipo": "basic"})

