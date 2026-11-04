from datetime import date

import fastapi
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session # type: ignore

from app import models
from app.database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = fastapi.FastAPI(title="Organizador de búsqueda laboral")


class PostulacionNueva(BaseModel):
    titulo: str
    empresa: str
    estado: str = "Pendiente"
    fecha_postulacion: date
    enlace: str
    rol: str


class PostulacionRespuesta(PostulacionNueva):
    id: int

    model_config = ConfigDict(from_attributes=True)


@app.get("/health")
def check_health():
    return {"status": "ok"}


@app.post("/postulaciones", response_model=PostulacionRespuesta)
def crear_postulacion(
    datos: PostulacionNueva,
    db: Session = fastapi.Depends(get_db),
):
    nueva_postulacion = models.Postulacion(**datos.model_dump())

    db.add(nueva_postulacion)
    db.commit()
    db.refresh(nueva_postulacion)

    return nueva_postulacion


@app.get("/postulaciones", response_model=list[PostulacionRespuesta])
def listar_postulaciones(db: Session = fastapi.Depends(get_db)):
    return db.query(models.Postulacion).all() 