from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api_router import api_router
from app.core.config import settings
from app.db.migrations import initialize_database

initialize_database()

app = FastAPI(title="NAI Study API", version="1.0.0")
frontend_origins = {settings.frontend_origin.rstrip("/")}
if "localhost" in settings.frontend_origin:
    frontend_origins.add(settings.frontend_origin.replace("localhost", "127.0.0.1").rstrip("/"))
elif "127.0.0.1" in settings.frontend_origin:
    frontend_origins.add(settings.frontend_origin.replace("127.0.0.1", "localhost").rstrip("/"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(frontend_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.exception_handler(RuntimeError)
async def runtime_error_handler(_, exc: RuntimeError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.get("/health")
def health():
    return {"status": "ok", "app": "NAI Study"}
