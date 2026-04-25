from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.database import init_db
    await init_db()
    yield


app = FastAPI(title="ContextHaus API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.properties import router as properties_router
app.include_router(properties_router, prefix="/api/properties", tags=["properties"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "contexthaus"}


@app.get("/api/test-gemini")
async def test_gemini():
    from app.core.llm import generate, FLASH
    result = await generate(prompt="Reply with exactly: ContextHaus is live.", model=FLASH)
    return {"response": result}