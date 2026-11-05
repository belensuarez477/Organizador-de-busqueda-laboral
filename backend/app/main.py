from datetime import date, datetime, timezone
from enum import Enum
import unicodedata

import fastapi
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator
from sqlalchemy.orm import Session # type: ignore

from app import models
from app.database import get_db


app = fastapi.FastAPI(title="Organizador de búsqueda laboral")

# Además de letras: espacios y signos habituales en nombres (Jr., Back-end, AT&T)
CARACTERES_PERMITIDOS = " .,-'&/()"


class EstadoPostulacion(str, Enum):
    CV_ENVIADO = "CV enviado"
    EN_REVISION = "En etapa de revisión"
    EN_ENTREVISTA = "En entrevista"
    FINALIZADO = "Finalizado"
    RECHAZADO = "Rechazado"


class PostulacionNueva(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    titulo: str = Field(min_length=1, max_length=200)
    empresa: str = Field(min_length=1, max_length=200)
    estado: EstadoPostulacion = EstadoPostulacion.CV_ENVIADO
    fecha_postulacion: date
    enlace: str = Field(min_length=1, max_length=500)
    rol: str = Field(min_length=1, max_length=100)

    @field_validator("titulo", mode="before")
    @classmethod
    def normalizar_titulo(cls, valor):
        # Antes de validar el largo: recorta extremos y junta espacios repetidos
        if isinstance(valor, str):
            return " ".join(valor.split())
        return valor

    @field_validator("titulo")
    @classmethod
    def titulo_valido(cls, valor: str) -> str:
        if any(unicodedata.category(c).startswith("C") for c in valor):
            raise ValueError("Contiene caracteres de control no permitidos")
        # RN-002: debe tener al menos una letra o un número
        if not any(c.isalnum() for c in valor):
            raise ValueError("Debe contener al menos una letra o un número")
        return valor

    @field_validator("empresa", "enlace", "rol")
    @classmethod
    def texto_no_vacio(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("No puede estar vacío")
        return valor

    @field_validator("empresa", "rol")
    @classmethod
    def sin_numeros(cls, valor: str) -> str:
        if any(caracter.isdigit() for caracter in valor):
            raise ValueError("No puede contener números")
        if not all(c.isalpha() or c in CARACTERES_PERMITIDOS for c in valor):
            raise ValueError("Solo puede contener letras")
        return valor


class PostulacionRespuesta(PostulacionNueva):
    id: int

    model_config = ConfigDict(from_attributes=True)


class NotaNueva(BaseModel):
    contenido: str = Field(max_length=models.CONTENIDO_NOTA_MAX)

    @field_validator("contenido")
    @classmethod
    def contenido_no_vacio(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("El contenido no puede estar vacío")
        return valor


class NotaRespuesta(BaseModel):
    id: int
    contenido: str
    fecha_creacion: datetime
    postulacion_id: int

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("fecha_creacion")
    def serializar_fecha(self, valor: datetime) -> str:
        return valor.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


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


@app.post(
    "/postulaciones/{postulacion_id}/notas",
    response_model=NotaRespuesta,
    status_code=201,
)
def crear_nota(
    postulacion_id: int,
    datos: NotaNueva,
    db: Session = fastapi.Depends(get_db),
):
    obtener_postulacion_o_404(postulacion_id, db)

    nota = models.Nota(contenido=datos.contenido, postulacion_id=postulacion_id)
    db.add(nota)
    db.commit()
    db.refresh(nota)

    return nota


@app.get(
    "/postulaciones/{postulacion_id}/notas",
    response_model=list[NotaRespuesta],
)
def listar_notas(postulacion_id: int, db: Session = fastapi.Depends(get_db)):
    obtener_postulacion_o_404(postulacion_id, db)

    return (
        db.query(models.Nota)
        .filter(models.Nota.postulacion_id == postulacion_id)
        .order_by(models.Nota.fecha_creacion.desc(), models.Nota.id.desc())
        .all()
    )


@app.delete("/postulaciones/{postulacion_id}", status_code=204)
def eliminar_postulacion(
    postulacion_id: int,
    db: Session = fastapi.Depends(get_db),
):
    postulacion = obtener_postulacion_o_404(postulacion_id, db)

    db.delete(postulacion)
    db.commit()
