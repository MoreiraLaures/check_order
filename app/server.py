import os
import tempfile
import threading
import time

from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from app.clients.piedadmin import PiedAdminClient
from app.modules.xlsx_parser import parse_xls
from app.modules.order_checker import check_order
from app.modules.report_writer import save_report
from app.paths import BUNDLE_DIR, RUNTIME_DIR

load_dotenv(os.path.join(RUNTIME_DIR, ".env"))

templates = Jinja2Templates(directory=os.path.join(BUNDLE_DIR, "app", "templates"))

app = FastAPI(title="Check Order")

# --- Watchdog: encerra o processo quando o browser fechar ---
_last_ping = time.time()


def _watchdog():
    time.sleep(20)          # grace period para o browser abrir
    while True:
        time.sleep(3)
        if time.time() - _last_ping > 10:
            os._exit(0)     # encerra o processo inteiro


threading.Thread(target=_watchdog, daemon=True).start()


def _render(request: Request, template: str, **ctx):
    return templates.TemplateResponse(request, template, ctx)


@app.get("/ping")
async def ping():
    global _last_ping
    _last_ping = time.time()
    return JSONResponse({"ok": True})


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return _render(request, "index.html")


@app.post("/verificar", response_class=HTMLResponse)
async def verificar(request: Request, file: UploadFile = File(...)):
    token = os.getenv("TOKEN")
    if not token:
        return _render(request, "result.html", error="TOKEN não configurado no .env", result=None)

    # Salva o upload em arquivo temporário (xlrd exige path em disco)
    suffix = os.path.splitext(file.filename)[1] or ".xls"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    # Substitui o nome temporário pelo nome original para extração do código
    named_path = os.path.join(os.path.dirname(tmp_path), file.filename)
    os.rename(tmp_path, named_path)

    try:
        xls = parse_xls(named_path)
    except Exception as exc:
        return _render(request, "result.html", error=f"Erro ao ler o arquivo: {exc}", result=None)
    finally:
        if os.path.exists(named_path):
            os.unlink(named_path)

    try:
        async with PiedAdminClient(token=token) as client:
            pedido = await client.buscar_pedido(xls.cell_code)
    except Exception as exc:
        return _render(request, "result.html", error=f"Erro na API: {exc}", result=None)

    result = check_order(xls, pedido)
    save_report(result, output_dir=os.path.join(RUNTIME_DIR, "response"))

    return _render(request, "result.html", result=result, error=None)
