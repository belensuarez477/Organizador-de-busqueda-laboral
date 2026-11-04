from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

CONTENIDO_NOTA_MAX = 2000


def ahora_utc() -> datetime:
    # SQLite no guarda zona horaria: se guarda en UTC sin tzinfo
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


class Postulacion(Base):
    __tablename__ = "postulaciones"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    titulo: Mapped[str] = mapped_column(String(200))
    empresa: Mapped[str] = mapped_column(String(200))
    estado: Mapped[str] = mapped_column(String(50), default="CV enviado")
    fecha_postulacion: Mapped[date] = mapped_column(Date)
    enlace: Mapped[str] = mapped_column(String(500))
    rol: Mapped[str] = mapped_column(String(100))

    notas: Mapped[list["Nota"]] = relationship(
        back_populates="postulacion", cascade="all, delete-orphan"
    )


class Nota(Base):
    __tablename__ = "notas"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    contenido: Mapped[str] = mapped_column(String(CONTENIDO_NOTA_MAX))
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, default=ahora_utc)
    postulacion_id: Mapped[int] = mapped_column(
        ForeignKey("postulaciones.id"), index=True
    )

    postulacion: Mapped[Postulacion] = relationship(back_populates="notas")
