from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Postulacion(Base):
    __tablename__ = "postulaciones"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    titulo: Mapped[str] = mapped_column(String(120), nullable=False)
    empresa: Mapped[str] = mapped_column(String(120), nullable=False)
    estado: Mapped[str] = mapped_column(
        String(50),
        default="Pendiente",
        nullable=False,
    )
    fecha_postulacion: Mapped[date] = mapped_column(Date, nullable=False)
    enlace: Mapped[str] = mapped_column(String(500), nullable=False)
    rol: Mapped[str] = mapped_column(String(120), nullable=False)

    