import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.v1.deps import get_optional_user
from app.models.users import User
from app.rag.search import perform_rag_search
from app.schemas.ai import AISearchRequest, AISearchResponse

router = APIRouter(prefix="/ai", tags=["GenAI RAG Search & Assistant"])


@router.post("/search", response_model=AISearchResponse)
async def ai_rag_search(
    body: AISearchRequest,
    current_user: User | None = Depends(get_optional_user),
):
    """GenAI Natural Language Search endpoint with candidate-grounded explanations."""
    user_id = current_user.id if current_user else None
    return await perform_rag_search(query=body.query, user_id=user_id, k=body.k)


@router.post("/chat")
async def ai_chat_stream(
    body: AISearchRequest,
    current_user: User | None = Depends(get_optional_user),
):
    """SSE Token Streaming conversational AI assistant endpoint."""
    user_id = current_user.id if current_user else None
    rag_res = await perform_rag_search(query=body.query, user_id=user_id, k=body.k)

    async def event_generator() -> AsyncGenerator[str, None]:
        # Event 1: Intent parsed
        intent_data = rag_res.intent.model_dump() if rag_res.intent else {}
        yield f"event: intent\ndata: {json.dumps(intent_data)}\n\n"

        # Event 2: Intro stream
        if rag_res.intro:
            words = rag_res.intro.split(" ")
            for w in words:
                yield f"event: token\ndata: {json.dumps({'token': w + ' '})}\n\n"

        # Event 3: Final JSON items payload
        items_payload = [item.model_dump(mode="json") for item in rag_res.items]
        yield f"event: results\ndata: {json.dumps({'items': items_payload})}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
