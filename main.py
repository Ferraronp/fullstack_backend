from fastapi import FastAPI
from db.database import Base, engine
from routers import users, categories, operations, admin, seo, analysis
from starlette.middleware.cors import CORSMiddleware
from services.s3_service import ensure_bucket

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Personal Finance Tracker API (with Auth)")

@app.on_event("startup")
def startup():
    ensure_bucket()

FRONTEND_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(categories.router)
app.include_router(operations.router)
app.include_router(admin.router)
app.include_router(seo.router)
app.include_router(analysis.router)


@app.get("/")
def root():
    return {"message": "Finance API with Auth is running"}
# python -m pytest tests/ --cov=. --cov-report=term-missing -q