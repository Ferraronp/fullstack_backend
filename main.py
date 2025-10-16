from fastapi import FastAPI
from database import Base, engine
from routers import categories, operations

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Personal Finance Tracker API")

app.include_router(categories.router)
app.include_router(operations.router)


@app.get("/")
def root():
    return {"message": "Finance API is running 🚀"}
