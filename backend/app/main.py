import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.logging import setup_logging

from app.db.base_class import Base
from app.db.session import engine

from app.models.user import User
from app.models.message import Message
from app.models.chat import Chat
from app.models.pinned_message import PinnedMessage
from app.models.file import File
from app.models.user_block import UserBlock
from app.models.message_deletion import MessageDeletion
from app.models.reaction import MessageReaction
from app.models.chat_deletion import ChatDeletion

from app.api import auth, chat, message, user, file, websocket_routes


setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup")

    Base.metadata.create_all(bind=engine)

    logger.info("Database tables initialized")

    yield

    logger.info("Application shutdown")


app = FastAPI(
    title="Messenger API",
    lifespan=lifespan,
)
logger.info("FastAPI application initialized")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://dae9-72-56-42-19.ngrok-free.app",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    try:
        response = await call_next(request)

        duration = round(time.time() - start_time, 3)

        logger.info(
            "%s %s -> %s (%ss)",
            request.method,
            request.url.path,
            response.status_code,
            duration,
        )

        return response

    except Exception:
        duration = round(time.time() - start_time, 3)

        logger.exception(
            "%s %s -> ERROR (%ss)",
            request.method,
            request.url.path,
            duration,
        )

        raise


# Routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router)
app.include_router(message.router)
app.include_router(user.router)
app.include_router(websocket_routes.router)
app.include_router(file.router)
logger.info("API routers initialized")

# Static files
app.mount("/storage", StaticFiles(directory="storage"), name="storage")
app.mount("/static", StaticFiles(directory="../static"), name="static")
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
logger.info("Static files mounted")

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception,
):
    logger.exception(
        "Unhandled application exception: %s %s",
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )