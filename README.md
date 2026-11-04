# Organizador-de-busqueda-laboral

## Backend

Desde la carpeta `backend`, con el entorno virtual activado:

```powershell
pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --reload
```

## Migraciones (Alembic)

Las tablas se crean y modifican con migraciones; la app ya no usa `create_all()`.

```powershell
alembic revision --autogenerate -m "descripcion del cambio"
alembic upgrade head
```

Revisá siempre el archivo generado en `backend/alembic/versions/` antes de aplicarlo.