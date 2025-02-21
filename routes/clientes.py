from fastapi import APIRouter, Depends, HTTPException
from services.db_service import get_cliente_por_cpf, get_dividas_por_cpf
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

@router.get("/")
def buscar_cliente(cpf: str, token: str = Depends(oauth2_scheme)):
    """
    Retorna informações de um cliente pelo CPF ou CNPJ.
    """
    cliente = get_cliente_por_cpf(cpf)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente

@router.get("/dividas")
def buscar_dividas_cliente(cpf: str, token: str = Depends(oauth2_scheme)):
    """
    Retorna todas as dívidas de um cliente pelo CPF ou CNPJ.
    """
    cliente, dividas = get_dividas_por_cpf(cpf)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    if not dividas:
        raise HTTPException(status_code=404, detail="Nenhuma dívida encontrada")
    
    return {"cliente": cliente, "dividas": dividas}
