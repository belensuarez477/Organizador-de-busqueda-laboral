from datetime import date

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Postulacion(Base):
    __tablename__ = "postulaciones"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    titulo: Mapped[str] = mapped_column(String(200))
    empresa: Mapped[str] = mapped_column(String(200))
    estado: Mapped[str] = mapped_column(String(50), default="CV enviado")
    fecha_postulacion: Mapped[date] = mapped_column(Date)
    enlace: Mapped[str] = mapped_column(String(500))
    rol: Mapped[str] = mapped_column(String(100))
