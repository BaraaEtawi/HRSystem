import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import get_allowed_origins
from app.api.v1 import auth_router, chat_router
from app.core.logging_config import setup_rotating_file_logger

app = FastAPI(
    title="Rubix Chat API",
    swagger_ui_parameters={"persistAuthorization": True},
)


setup_rotating_file_logger()

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")

app.mount("/", StaticFiles(directory="static", html=True), name="static")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = id(request)
    try:
        response = await call_next(request)
        return response
    except HTTPException:
        raise
    except Exception as e:
        return FastAPI().responses.JSONResponse(
            status_code=500,
            content={"detail": "internal server error", "request_id": request.state.request_id},
        )