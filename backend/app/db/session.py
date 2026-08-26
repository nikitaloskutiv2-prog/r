from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.core.config import DATABASE_URL


# 🚀 Engine
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    }
)


# 🔥 Включаем FOREIGN KEY constraints для SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):

    cursor = dbapi_connection.cursor()

    cursor.execute("PRAGMA foreign_keys=ON")

    cursor.close()


# 🏭 Фабрика сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# 🔌 Dependency для FastAPI
def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()