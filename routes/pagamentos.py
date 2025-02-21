from fastapi import APIRouter, HTTPException , Depends
from pydantic import BaseModel
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import random
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer
import segno


load_dotenv()

# Conexão com MongoDB
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["banco-dividas"]

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

class PagamentoRequest(BaseModel):
    cpf: str
    ids_dividas: list[int]   # Agora aceita múltiplos IDs de dívida


class BoletoResponse(BaseModel):
    id_pagamento: str
    boleto_url: str
    codigo_barras: str
    valor_total: float
    status: str

class PagamentoResponse(BaseModel):
    id_pagamento: str
    valor_total: float
    boleto_url: str
    codigo_barras: str
    pix_url: str
    qr_code: str
    status: str




def registrar_historico_pagamento(ids_dividas, id_pagamento, metodo, status):
    """
    Adiciona um registro no histórico de interações de cada dívida.
    Se o campo 'historico_interacoes' não existir, cria como array antes de adicionar um novo item.
    """
    for id_divida in ids_dividas:
        # Primeiro, verifica se o campo já é um array. Se não for, corrige.
        db["dividas"].update_one(
            {"contrato": id_divida, "historico_interacoes": {"$exists": False}},
            {"$set": {"historico_interacoes": []}}
        )

        # Agora, adiciona o novo histórico de pagamento.
        db["dividas"].update_one(
            {"contrato": id_divida},
            {
                "$push": {
                    "historico_interacoes": {
                        "id_pagamento": id_pagamento,
                        "data_pagamento": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                        "metodo": metodo,
                        "status": status
                    }
                }
            }
        )



@router.get("/status/{id_pagamento}")
def status_pagamento(id_pagamento: str, token: str = Depends(oauth2_scheme)):
    """
    Consulta o status de um pagamento.
    """
    pagamento = db["pagamentos"].find_one({"contrato": id_pagamento})

    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado.")

    return {
        "id_pagamento": id_pagamento,
        "status": pagamento["status"],
        "valor_total": pagamento["valor_total"],
        "ids_dividas": pagamento["ids_dividas"]
    }


@router.get("/dividas-pendentes/{cpf}")
def listar_dividas_pendentes(cpf: str , token: str = Depends(oauth2_scheme)):
    """
    Lista todas as dívidas pendentes de um cliente com base no CPF.
    """
    cliente = db["clientes"].find_one({"cpf": cpf})

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    # Pegando os IDs das dívidas do cliente
    ids_dividas = cliente.get("dividas", [])

    # Buscando apenas as dívidas com status "em aberto"
    dividas_pendentes = list(db["dividas"].find({"contrato": {"$in": ids_dividas}, "status": "em aberto"}))

    if not dividas_pendentes:
        raise HTTPException(status_code=404, detail="Nenhuma dívida pendente encontrada.")

    return {"cpf": cpf, "dividas_pendentes": dividas_pendentes}


@router.post("/confirmar-pagamento/{id_pagamento}")
def confirmar_pagamento(id_pagamento: str , token: str = Depends(oauth2_scheme)):
    """
    Confirma o pagamento e atualiza o status da dívida para quitado.
    """
    pagamento = db["pagamentos"].find_one({"_id": id_pagamento})


    if not pagamento:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado.")

    if pagamento["status"] == "aprovado":
        raise HTTPException(status_code=400, detail="Pagamento já foi aprovado anteriormente.")

    # Atualizar status do pagamento
    db["pagamentos"].update_one({"_id": id_pagamento}, {"$set": {"status": "aprovado"}})

    # Atualizar status das dívidas pagas
    db["dividas"].update_many(
        {"_id": {"$in": pagamento["ids_dividas"]}},
        {"$set": {"status": "quitado"}}
    )

    # Registrar histórico da transação
    for id_divida in pagamento["ids_dividas"]:
        db["dividas"].update_one(
            {"contrato": id_divida},
            {"$push": {"historico_interacoes": {"acao": "pagamento confirmado", "id_pagamento": id_pagamento}}}
        )

    return {"id_pagamento": id_pagamento, "status": "aprovado", "mensagem": "Pagamento confirmado com sucesso."}

