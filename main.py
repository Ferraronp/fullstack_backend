from fastapi import FastAPI
from db.database import Base, engine
from routers import users, categories, operations, admin
from starlette.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Personal Finance Tracker API (with Auth)")

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


@app.get("/")
def root():
    return {"message": "Finance API with Auth is running"}
