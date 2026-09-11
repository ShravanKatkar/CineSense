import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_optional_user
from app.db.session import get_db_session
from app.models.users import User
from app.rag.agent import run_agent, stream_agent_events
from app.rag.search import perform_rag_search
from app.schemas.ai import AISearchRequest, AISearchResponse

router = APIRouter(prefix="/ai", tags=["GenAI RAG Search & Assistant"])


@router.post("/search", response_model=AISearchResponse)
async def ai_rag_search(
    body: AISearchRequest,
    current_user: User | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_db_session),
):
    """GenAI Natural Language Search endpoint with candidate-grounded explanations."""
    user_id = current_user.id if current_user else None
    return await perform_rag_search(query=body.query, user_id=user_id, k=body.k)


@router.post("/chat")
async def ai_chat_stream(
    body: AISearchRequest,
    current_user: User | None = Depends(get_optional_user),
):
    """SSE Token Streaming conversational AI assistant endpoint with live tool calling."""
    user_id = current_user.id if current_user else None
    return StreamingResponse(
        stream_agent_events(query=body.query, user_id=user_id),
        media_type="text/event-stream",
    )
