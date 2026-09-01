import os
from typing import Annotated

from fastapi import Depends

from .provider import OpenAITicketAssistant
from .service import DisabledTicketAssistant, TicketAssistant


def get_ticket_assistant() -> TicketAssistant:
    provider = os.getenv("AI_PROVIDER", "disabled").strip().lower()
    api_key = os.getenv("AI_API_KEY", "").strip()
    model = os.getenv("AI_MODEL", "").strip()
    try:
        timeout_seconds = float(os.getenv("AI_TIMEOUT_SECONDS", "15"))
    except ValueError:
        return DisabledTicketAssistant()

    if provider != "openai" or not api_key or not model or timeout_seconds <= 0:
        return DisabledTicketAssistant()
    return OpenAITicketAssistant(
        api_key=api_key, model=model, timeout_seconds=timeout_seconds
    )


TicketAssistantDependency = Annotated[TicketAssistant, Depends(get_ticket_assistant)]
