from fastapi import FastAPI, Request, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import toml
import os
import httpx
from typing import Dict
from pathlib import Path

load_dotenv()  # Load .env variables
ENV_PATH = ".env"

app = FastAPI()
# Middleware untuk mengizinkan CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # sesuaikan jika perlu
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Load .env variables
BASE_URL = os.getenv("BASE_URL", "https://webapps.bps.go.id/olah/seruti/resource/query/executeRaw")
CSRF_TOKEN = os.getenv("CSRF_TOKEN", "")
XSRF_TOKEN = os.getenv("XSRF_TOKEN", "")
COOKIES = os.getenv("COOKIES", "")

class QueryParams(BaseModel):
    kd_prov: str
    kd_kab: str
    tw: str
    raw: str
    limit: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    query_list = toml.load(os.path.join(BASE_DIR, "queries", "query_list.toml"))["query"]
    return templates.TemplateResponse("index.html", {"request": request, "query_list": query_list})

@app.get("/get-query/{query_id}")
async def get_query(query_id: str):
    queries = toml.load(os.path.join(BASE_DIR, "queries", "query_list.toml"))["query"]
    for q in queries:
        if q["id"] == query_id:
            return q
    return JSONResponse({"error": "Query not found"}, status_code=404)

@app.post("/proxy-seruti")
async def proxy(params: QueryParams):
    body = {
        "kd_prov": params.kd_prov,
        "kd_kab": params.kd_kab,
        "tw": params.tw,
        "raw": params.raw,
        "limit": params.limit
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "x-csrf-token": CSRF_TOKEN,
        "x-requested-with": "XMLHttpRequest",
        "x-xsrf-token": XSRF_TOKEN,
        "cookie": COOKIES,
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "cors"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(BASE_URL, headers=headers, json=body)
            content_type = response.headers.get("content-type", "")
            text = response.text

            # DETEKSI TIPE RESPONSE
            if "application/json" in content_type:
                return response.json()
            else:
                return {
                    "error": "Response bukan JSON",
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "text_snippet": text[:1000]  # tampilkan isi 
                }
    except Exception as e:
        return {"error": str(e)}
    
def update_env_file(new_data: dict):
    """Update file .env dengan data baru"""
    if not os.path.exists(ENV_PATH):
        raise FileNotFoundError(f"{ENV_PATH} tidak ditemukan")

    with open(ENV_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Buat salinan yang akan ditulis ulang
    updated_lines = []
    for line in lines:
        if line.startswith("CSRF_TOKEN="):
            updated_lines.append(f"CSRF_TOKEN='{new_data.get('CSRF_TOKEN', '').strip()}'\n")
        elif line.startswith("XSRF_TOKEN="):
            updated_lines.append(f"XSRF_TOKEN='{new_data.get('XSRF_TOKEN', '').strip()}'\n")
        elif line.startswith("COOKIES="):
            updated_lines.append(f"COOKIES='{new_data.get('COOKIES', '').strip()}'\n")
        else:
            updated_lines.append(line)

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(updated_lines)

@app.post("/update-env")
async def update_env(request: Request):
    try:
        data = await request.json()
        csrf = data.get("CSRF_TOKEN")
        xsrf = data.get("XSRF_TOKEN")
        cookies = data.get("COOKIES")

        if not (csrf and xsrf and cookies):
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Missing one or more required fields"}
            )

        print("=== Data Diterima ===")
        print(f"CSRF_TOKEN: {csrf}")
        print(f"XSRF_TOKEN: {xsrf}")
        print(f"COOKIES   : {cookies}")
        print("=====================\n")

        update_env_file(data)

        return JSONResponse(
            status_code=200,
            content={"status": "success", "message": ".env updated", "updated": data}
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )
