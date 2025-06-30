from fastapi import FastAPI, Request, Body, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import pandas as pd
import toml
import os
import httpx
from typing import Dict
from pathlib import Path

COOKIES_PATH = os.path.join(os.path.dirname(__file__), "queries/cookies.txt")

app = FastAPI()
# Middleware untuk mengizinkan CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # sesuaikan jika perlu
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Fungsi pembaca dari XLSX
def load_queries_from_excel(path: str):
    df = pd.read_excel(path)
    queries = []
    for _, row in df.iterrows():
        queries.append({
            "id": str(row["id"]),
            "judul": row["judul"],
            "keterangan": row.get("keterangan", ""),
            "raw": row["sql"],
            "limit": str(row.get("limit", "1000")),
            "tipe": row.get("tipe", "tabel")
        })
    return queries

# fungsi untuk mengambil token
def load_tokens():
    """Baca CSRF_TOKEN, XSRF_TOKEN, dan COOKIES dari cookies.txt"""
    tokens = {"CSRF_TOKEN": "", "XSRF_TOKEN": "", "COOKIES": ""}
    if os.path.exists(COOKIES_PATH):
        with open(COOKIES_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    if key in tokens:
                        tokens[key] = value.strip()
    return tokens

BASE_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

BASE_URL = "https://webapps.bps.go.id/olah/seruti/resource/query/executeRaw"

class QueryParams(BaseModel):
    kd_prov: str
    kd_kab: str
    tw: str
    raw: str
    limit: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    query_list = load_queries_from_excel(os.path.join(BASE_DIR, "queries", "query_list.xlsx"))
    return templates.TemplateResponse("index.html", {"request": request, "query_list": query_list})

@app.get("/get-query/{query_id}")
async def get_query(query_id: str):
    queries = load_queries_from_excel(os.path.join(BASE_DIR, "queries", "query_list.xlsx"))
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

    tokens = load_tokens()
    headers = {
        "accept": "application/json, text/plain, */*",
        "content-type": "application/json",
        "x-csrf-token": tokens["CSRF_TOKEN"],
        "x-requested-with": "XMLHttpRequest",
        "x-xsrf-token": tokens["XSRF_TOKEN"],
        "cookie": tokens["COOKIES"],
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
    
def update_cookie_file(new_data: dict):
    """Update cookies.txt"""
    lines = [
        f"CSRF_TOKEN={new_data.get('CSRF_TOKEN', '').strip()}\n",
        f"XSRF_TOKEN={new_data.get('XSRF_TOKEN', '').strip()}\n",
        f"COOKIES={new_data.get('COOKIES', '').strip()}\n"
    ]
    with open(COOKIES_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)

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

        update_cookie_file(data)

        return JSONResponse(
            status_code=200,
            content={"status": "success", "message": ".env updated", "updated": data}
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )
    

@app.get("/set-cookies-form", response_class=HTMLResponse)
async def show_cookies_form(request: Request):
    return templates.TemplateResponse("set_cookies.html", {"request": request})


@app.post("/set-cookies-form", response_class=HTMLResponse)
async def submit_cookies_form(
    request: Request,
    CSRF_TOKEN: str = Form(...),
    XSRF_TOKEN: str = Form(...),
    COOKIES: str = Form(...)
):
    new_data = {
        "CSRF_TOKEN": CSRF_TOKEN,
        "XSRF_TOKEN": XSRF_TOKEN,
        "COOKIES": COOKIES
    }

    update_cookie_file(new_data)

    return templates.TemplateResponse("set_cookies.html", {
        "request": request,
        "message": "Cookies berhasil diperbarui!",
        "updated": new_data
    })