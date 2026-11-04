from datetime import date
from enum import Enum

import fastapi
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session # type: ignore

from app import models
from app.database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = fastapi.FastAPI(title="Organizador de búsqueda laboral")


class EstadoPostulacion(str, Enum):
    CV_ENVIADO = "CV enviado"
    EN_REVISION = "En etapa de revisión"
    EN_ENTREVISTA = "En entrevista"
    FINALIZADO = "Finalizado"
    RECHAZADO = "Rechazado"


class PostulacionNueva(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    titulo: str
    empresa: str
    estado: EstadoPostulacion = EstadoPostulacion.CV_ENVIADO
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


def obtener_postulacion_o_404(postulacion_id: int, db: Session):
    postulacion = db.get(models.Postulacion, postulacion_id)
    if postulacion is None:
        raise fastapi.HTTPException(status_code=404, detail="Postulación no encontrada")
    return postulacion


@app.get("/postulaciones/{postulacion_id}", response_model=PostulacionRespuesta)
def obtener_postulacion(
    postulacion_id: int,
    db: Session = fastapi.Depends(get_db),
):
    return obtener_postulacion_o_404(postulacion_id, db)


@app.put("/postulaciones/{postulacion_id}", response_model=PostulacionRespuesta)
def actualizar_postulacion(
    postulacion_id: int,
    datos: PostulacionNueva,
    db: Session = fastapi.Depends(get_db),
):
    postulacion = obtener_postulacion_o_404(postulacion_id, db)

    for campo, valor in datos.model_dump().items():
        setattr(postulacion, campo, valor)

    db.commit()
    db.refresh(postulacion)

    return postulacion


@app.delete("/postulaciones/{postulacion_id}", status_code=204)
def eliminar_postulacion(
    postulacion_id: int,
    db: Session = fastapi.Depends(get_db),
):
    postulacion = obtener_postulacion_o_404(postulacion_id, db)

    db.delete(postulacion)
    db.commit()
