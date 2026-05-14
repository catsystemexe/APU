from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.api.chat import router as chat_router
from backend.api.notepad import router as notepad_router

app = FastAPI(title="APU ZUS P1")

# Static assets (CSS/JS)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API
app.include_router(chat_router, prefix="/api")
app.include_router(notepad_router)


# UI
@app.get("/")
def root():
    return FileResponse("frontend/index.html")


# Health
@app.get("/health")
def health():
    return {"status": "ok"}
