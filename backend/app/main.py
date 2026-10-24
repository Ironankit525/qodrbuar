from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import config
from .routes import router

app = FastAPI(title="Wind forecast monitor", version="1.0.0")
app.include_router(router)

# In the Docker image the built React app is served by the API itself (one origin, one port).
# In local development the Vite dev server serves it instead and proxies /api here.
if config.STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=config.STATIC_DIR, html=True), name="frontend")
