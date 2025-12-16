# src/todolist/routes/ai.py
from fastapi import APIRouter, Depends, HTTPException, Query
from src.todolist.services.ai_nlp.ai_service import suggest_completion
from src.todolist.auth.service import CurrentUser 

ai_router = APIRouter()


@ai_router.get("/suggest")
async def suggest(
    current_user: CurrentUser, 
    prefix: str = Query(..., min_length=1),
    # 👇 NEW PARAMETER: Accept context (list title) from URL
    context: str = Query(None, description="Title of the todo list") 
):
    user_id = getattr(current_user, "id", None) if current_user else None
    
    suggestion = await suggest_completion(prefix, user_id=user_id, context=context)
    
    return {"input": prefix, "suggestion": suggestion}
