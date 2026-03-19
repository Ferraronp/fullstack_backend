from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from db.database import get_db
from utils.auth import get_current_user
from models import models
from services.groq_service import analyze_operations
import crud.operation

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.get("/ai")
async def ai_analysis(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
):
    """Анализирует последние операции пользователя через Groq LLM."""
    result = crud.operation.get_operations(
        db, current_user,
        sort_by="date", sort_order="desc",
        page=1, page_size=limit,
    )
    operations = [
        {
            "date": str(op.date),
            "amount": op.amount,
            "comment": op.comment,
            "category": {"name": op.category.name} if op.category else None,
        }
        for op in result["items"]
    ]

    try:
        analysis = await analyze_operations(operations)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return {"analysis": analysis, "operations_count": len(operations)}
