from . import app
from .routes import llm_service

app.include_router(llm_service.router)


@app.get("/")
def read_root():
    return {"Hello": "World"}
