from fastapi import FastAPI

app = FastAPI(title="Organizador de búsqueda laboral")


@app.get("/health")
def check_health():
    return {"status": "ok"}