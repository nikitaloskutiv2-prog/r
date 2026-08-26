import os
import sys
import pytest

# conftest находится в backend/test/ -> хотим добавить backend/ в sys.path
TEST_DIR = os.path.abspath(os.path.dirname(__file__))        # .../backend/test
BACKEND_DIR = os.path.abspath(os.path.join(TEST_DIR, ".."))  # .../backend
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Тестовые env должны быть выставлены ДО импорта app
os.environ.setdefault("SECRET_KEY", "testsecret")
# Помещаем тестовую БД в backend/ (одна для всех тестов)
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_db_for_tests.db")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Теперь можно импортировать приложение
from app.main import app
from app.db.base_class import Base
from app.db.session import get_db as real_get_db

# Тестовая SQLite — файл лежит в BACKEND_DIR
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db_for_tests.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

# Переопределяем get_db для тестов
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[real_get_db] = override_get_db

# Отключаем rate limit в тестах, чтобы регистрация не падала с 429
try:
    from app.services import rate_limit_service

    rate_limit_service.check_register_rate_limit = lambda client_ip: True
    rate_limit_service.check_login_rate_limit = lambda client_ip, login: True

    rate_limit_service.record_registration = lambda client_ip: None
    rate_limit_service.record_failed_login = lambda client_ip, login: None
    rate_limit_service.reset_login_rate_limit = lambda client_ip, login: None
except Exception:
    pass

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()