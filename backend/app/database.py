import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# Guarda la base de datos dentro de la carpeta backend
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "organizador.db"

# Se puede cambiar con la variable de entorno DATABASE_URL (por ejemplo, PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH.as_posix()}")
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# Crea el motor de conexión
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if IS_SQLITE else {},
    pool_pre_ping=True,
)


if IS_SQLITE:
    # Ajustes de SQLite que se aplican en cada conexión nueva
    @event.listens_for(engine, "connect")
    def configure_sqlite(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")  # mejor concurrencia lectura/escritura
        cursor.execute("PRAGMA synchronous=NORMAL")  # más rápido, seguro con WAL
        cursor.execute("PRAGMA foreign_keys=ON")  # SQLite no valida claves foráneas por defecto
        cursor.close()


# Crea sesiones para consultar o guardar datos
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)


def get_db():
    """Abre una sesión por request y la cierra siempre al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Clase base para definir las tablas más adelante
class Base(DeclarativeBase):
    pass

from collections.abc import Generator
from sqlalchemy.orm import Session

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()