from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth import router as auth_router
from routes.clientes import router as clientes_router
from routes.pagamentos import router as pagamentos_router
from routes.boletos import router as boletos_router
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("🔹 AUTHORIZATION_URL: %s", os.getenv("AUTHORIZATION_URL"))
logger.info("🔹 TOKEN_URL: %s", os.getenv("TOKEN_URL"))

app = FastAPI(
    title="API de Cobranças Protegida",
    description="API com autenticação JWT via login e senha",
    version="0.2.0"
)

# CORS Configurado com segurança
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# Adicionar endpoint de saúde
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

# Registrar rotas
app.include_router(auth_router, prefix="/auth")
app.include_router(clientes_router, prefix="/clientes")
app.include_router(pagamentos_router, prefix="/pagamentos")
app.include_router(boletos_router, prefix="/boletos")