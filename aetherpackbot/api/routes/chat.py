"""Chat API routes."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from aetherpackbot.providers.base import ChatMessage, ChatRole

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat completion request."""

    message: str
    provider: str | None = None
    model: str | None = None
    system_prompt: str | None = None
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None


class ChatResponse(BaseModel):
    """Chat completion response."""

    content: str
    model: str
    provider: str
    usage: dict[str, int] | None = None


@router.post("")
async def chat(request: Request, body: ChatRequest) -> ChatResponse:
    """Send a chat completion request."""
    engine = request.app.state.engine
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    # Get provider
    provider_name = body.provider
    if provider_name:
        provider = engine.get_provider(provider_name)
    else:
        provider = engine.get_default_provider()

    if not provider:
        raise HTTPException(status_code=404, detail="No LLM provider available")

    # Build messages
    messages: list[ChatMessage] = []
    if body.system_prompt:
        messages.append(ChatMessage(role=ChatRole.SYSTEM, content=body.system_prompt))
    messages.append(ChatMessage(role=ChatRole.USER, content=body.message))

    # Build kwargs
    kwargs: dict = {}
    if body.model:
        kwargs["model"] = body.model
    if body.temperature is not None:
        kwargs["temperature"] = body.temperature
    if body.max_tokens is not None:
        kwargs["max_tokens"] = body.max_tokens

    try:
        response = await provider.chat(messages, **kwargs)
        return ChatResponse(
            content=response.content,
            model=response.model,
            provider=provider.name,
            usage=response.usage,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/stream")
async def chat_stream(request: Request, body: ChatRequest) -> StreamingResponse:
    """Stream a chat completion response."""
    engine = request.app.state.engine
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    provider = engine.get_default_provider()
    if not provider:
        raise HTTPException(status_code=404, detail="No LLM provider available")

    messages: list[ChatMessage] = []
    if body.system_prompt:
        messages.append(ChatMessage(role=ChatRole.SYSTEM, content=body.system_prompt))
    messages.append(ChatMessage(role=ChatRole.USER, content=body.message))

    async def generate():
        try:
            async for chunk in provider.chat_stream(messages):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
