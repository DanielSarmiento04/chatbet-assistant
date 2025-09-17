from fastapi import (
    APIRouter
)
from ..services.llm import (
    llm,
    STYLE_INSTRUCTIONS
)

router = APIRouter()

messages = [
    (
        "system",
        f"You are a helpful assistant. {STYLE_INSTRUCTIONS}",
    ),
]


@router.post("/chat")
async def chat_endpoint(user_message: str):
    messages.append(("user", user_message))
    response = llm.invoke(messages)
    # messages.append(("assistant", response.content))
    return {"response": response.content}