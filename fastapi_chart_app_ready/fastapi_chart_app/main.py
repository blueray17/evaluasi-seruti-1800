from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import httpx
import toml

load_dotenv()

app = FastAPI()
BASE_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Load token & cookie dari .env
BASE_URL = os.getenv("BASE_URL")
CSRF_TOKEN = os.getenv("CSRF_TOKEN").strip("'")
XSRF_TOKEN = os.getenv("XSRF_TOKEN").strip("'")
COOKIES = os.getenv("COOKIES").strip("'")

class QueryParams(BaseModel):
    kd_prov: str
    kd_kab: str
    tw: str
    raw: str
    limit: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    query_list = toml.load(os.path.join(BASE_DIR, "queries/query_list.toml"))["query"]
    return templates.TemplateResponse("index.html", {"request": request, "query_list": query_list})

@app.get("/get-query/{query_id}")
async def get_query(query_id: str):
    queries = toml.load(os.path.join(BASE_DIR, "queries/query_list.toml"))["query"]
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

    async with httpx.AsyncClient() as client:
        response = await client.post(BASE_URL, headers=headers, json=body)
        try:
            return response.json()
        except Exception:
            return {
                "error": "Response bukan JSON",
                "status_code": response.status_code,
                "text": response.text[:1000]
            }