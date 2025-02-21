from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["banco-dividas"]

def get_cliente_por_cpf(cpf: str):
    """
    Busca um cliente no banco de dados pelo CPF/CNPJ.
    Retorna apenas os campos essenciais.
    """
    cliente = db["clientes"].find_one({"cpf": cpf}, {"_id": 1, "nome": 1, "cpf": 1, "contato": 1, "endereco": 1})
    return cliente

def get_dividas_por_cpf(cpf: str):
    """
    Busca todas as dívidas de um cliente pelo CPF/CNPJ.
    """
    cliente = db["clientes"].find_one({"cpf": cpf}, {"_id": 1, "nome": 1, "cpf": 1})
    if not cliente:
        return None, None

    dividas = list(db["dividas"].find({"cliente_id": cliente["_id"]}, {"_id": 1, "valor": 1, "data_vencimento": 1, "status": 1, "contrato": 1}))
    return cliente, dividas
