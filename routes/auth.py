import os
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Form, status
from fastapi.security import OAuth2PasswordBearer, HTTPBasic, HTTPBasicCredentials
from services.auth_service import autenticar_usuario, criar_token
from pymongo import MongoClient

# Carregar variáveis do .env
load_dotenv()

# Conexão com o MongoDB
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["users-api"]

router = APIRouter()

# Configuração dos esquemas de autenticação
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
security = HTTPBasic()

@router.post("/token")
def login(
    grant_type: str = Form(...),
    username: str = Form(None),
    password: str = Form(None),
    client_id: str = Form(None),
    client_secret: str = Form(None),
):
    """
    Autentica o usuário de três formas:
    - grant_type=password → Autenticação de usuário com username/password
    - grant_type=client_credentials → Autenticação via client_id/client_secret para integrações externas
    - grant_type=authorization_code → Código de autorização do OAuth2
    """
    if grant_type == "password":
        if not username or not password:
            raise HTTPException(status_code=400, detail="Username e password são obrigatórios para grant_type=password")
        return autenticar_usuario(username, password)

    elif grant_type == "client_credentials":
        if not client_id or not client_secret:
            raise HTTPException(status_code=400, detail="Client ID e Client Secret são obrigatórios para grant_type=client_credentials")
        
        # Verifica as credenciais da integração no banco
        credencial = db["credenciais_integracao"].find_one({"client_id": client_id})
        if not credencial or credencial["client_secret"] != client_secret:
            raise HTTPException(status_code=401, detail="Credenciais inválidas para integração")

        return criar_token({"client_id": client_id, "tipo": "integração"})

    elif grant_type == "authorization_code":
        return criar_token({"authorization_code": "codigo_autorizacao"})

    else:
        raise HTTPException(status_code=400, detail="grant_type inválido. Use 'password', 'client_credentials' ou 'authorization_code'.")

@router.post("/token/basic")
def login(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Autentica o usuário via Basic Auth.
    """
    token = autenticar_usuario(credentials.username, credentials.password)
    if not token:
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")
    
    return {"access_token": token, "token_type": "bearer"}
