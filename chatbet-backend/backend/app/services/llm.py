"""
Legacy LLM service - this will be replaced by the new comprehensive service.
Keeping this temporarily for backward compatibility.
"""

from langchain_google_genai import (
    ChatGoogleGenerativeAI,
)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

STYLE_INSTRUCTIONS = "Use a conversational tone and write in a chat style without formal formatting or lists and do not use any emojis."
