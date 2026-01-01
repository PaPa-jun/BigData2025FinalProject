import time, requests
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .models import SearchRequest, SearchResponse, DownloadRequest, DownloadResponse
from .utils import execute_search, parse_query, rerank
from .db import HBaseDB


def create_app(db_cli: HBaseDB, configs: dict) -> FastAPI:
    app = FastAPI()

    origins = ["http://localhost", "http://localhost:8000"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

    @app.post("/api/search", response_model=SearchResponse)
    def search(request: SearchRequest):
        keywords = parse_query(request.query)
        results = execute_search(db_cli, configs["INDEX_TABLE_NAME"], keywords)
        return rerank(request, results)

    @app.post("/api/download", response_model=DownloadResponse)
    def download(request: DownloadRequest):
        base_url = f"{configs['HDFS_URL']}/webhdfs/v1{request.path}"
        params = {"op": "OPEN", "user.name": configs["HDFS_USER"]}
        response = requests.get(
            base_url, params=params, allow_redirects=False, timeout=10
        )
        if response.status_code == 307:
            redirect_url = response.headers.get("Location")
            if not redirect_url:
                raise HTTPException(
                    status_code=500, detail="NameNode返回307状态码但未提供Location头"
                )
        if configs["REDIRECT"] is True:
            return DownloadResponse(
                download_url=redirect_url.replace("hadoop-master", "localhost")
            )
        else:
            return DownloadResponse(download_url=redirect_url)

    web_dir = Path(configs["WEB_DIR"])
    app.mount("/", StaticFiles(directory=web_dir, html=True), name="static")

    return app
