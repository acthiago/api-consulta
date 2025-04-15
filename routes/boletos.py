from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pymongo.database import Database
from services.db_service import get_db
import os
import random
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import segno

load_dotenv()

router = APIRouter()

class BoletoRequest(BaseModel):
    cpf: str
    ids_dividas: list[int]

class BoletoResponse(BaseModel):
    id_pagamento: str
    boleto_url: str
    codigo_barras: str
    pix_codigo: str
    valor_total: float
    status: str

def gerar_boleto_pdf(codigo_barras, pix_codigo, valor, vencimento, id_pagamento):
    """
    Função que gera um boleto em PDF com QR Code PIX.
    """
    try:
        nome_arquivo = f"/mnt/arquivos/boletos/boleto_{id_pagamento}.pdf"
        os.makedirs("boletos", exist_ok=True)

        c = canvas.Canvas(nome_arquivo, pagesize=letter)
        c.drawString(100, 750, "Boleto Bancário - Fake")
        c.drawString(100, 730, f"ID do Pagamento: {id_pagamento}")
        c.drawString(100, 710, f"Valor: R$ {valor:.2f}")
        c.drawString(100, 690, f"Vencimento: {vencimento}")
        c.drawString(100, 670, f"Código de Barras: {codigo_barras}")
        c.drawString(100, 650, "Pague com PIX:")

        qr = segno.make(pix_codigo)
        qr_filename = f"boletos/qrcode_{id_pagamento}.png"
        qr.save(qr_filename, scale=5)
        c.drawImage(qr_filename, 100, 500, width=150, height=150)
        c.save()
        os.remove(qr_filename)

        return nome_arquivo
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar boleto PDF: {e}")

@router.post("/gerar", response_model=BoletoResponse)
def gerar_boleto(pagamento: BoletoRequest, db: Database = Depends(get_db)):
    """
    Gera um boleto em PDF para pagamento de uma ou mais dívidas, incluindo QR Code PIX.
    """
    try:
        dividas = list(db["dividas"].find({"contrato": {"$in": pagamento.ids_dividas}}))
        if not dividas:
            raise HTTPException(status_code=404, detail="Nenhuma dívida encontrada para este cliente.")

        valor_total = sum(d["valor"] for d in dividas)
        vencimento = dividas[0]["data_vencimento"]
        codigo_barras = "".join(str(random.randint(0, 9)) for _ in range(48))
        id_pagamento = f"pg_{random.randint(1000, 9999)}"
        pix_codigo = f"00020126580014BR.GOV.BCB.PIX0114+5511999999995204000053039865802BR5913Cliente Teste6009SAO PAULO62140510ID{id_pagamento}6304"

        nome_arquivo = gerar_boleto_pdf(codigo_barras, pix_codigo, valor_total, vencimento, id_pagamento)

        db["pagamentos"].insert_one({
            "_id": id_pagamento,
            "cpf": pagamento.cpf,
            "ids_dividas": pagamento.ids_dividas,
            "metodo": "boleto",
            "boleto_url": f"/boletos/download/{id_pagamento}",
            "codigo_barras": codigo_barras,
            "pix_codigo": pix_codigo,
            "valor_total": valor_total,
            "status": "pendente"
        })

        return BoletoResponse(
            id_pagamento=id_pagamento,
            boleto_url=f"/boletos/download/{id_pagamento}",
            codigo_barras=codigo_barras,
            pix_codigo=pix_codigo,
            valor_total=valor_total,
            status="pendente"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar boleto: {e}")

@router.get("/download/{id_pagamento}")
def download_boleto(id_pagamento: str):
    """
    Endpoint para baixar o boleto em PDF.
    """
    try:
        nome_arquivo = f"/mnt/arquivos/boletos/boleto_{id_pagamento}.pdf"
        if not os.path.exists(nome_arquivo):
            raise HTTPException(status_code=404, detail="Boleto não encontrado.")
        return FileResponse(nome_arquivo, media_type="application/pdf", filename=f"boleto_{id_pagamento}.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao baixar boleto: {e}")
