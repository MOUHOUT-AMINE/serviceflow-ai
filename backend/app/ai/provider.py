import json

import httpx
from pydantic import ValidationError

from .schemas import TicketSuggestions
from .service import TicketAssistantError


class OpenAITicketAssistant:
    def __init__(self, *, api_key: str, model: str, timeout_seconds: float) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds

    def suggest(self, *, title: str, description: str) -> TicketSuggestions:
        payload = {
            "model": self._model,
            "instructions": (
                "You are a service-desk assistant. Analyze only the supplied ticket. "
                "Return concise, practical suggestions in the required JSON schema."
            ),
            "input": f"Ticket title:\n{title}\n\nTicket description:\n{description}",
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "ticket_suggestions",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "summary": {"type": "string"},
                            "suggested_priority": {
                                "type": "string",
                                "enum": ["low", "medium", "high"],
                            },
                            "recommended_action": {"type": "string"},
                        },
                        "required": [
                            "summary",
                            "suggested_priority",
                            "recommended_action",
                        ],
                        "additionalProperties": False,
                    },
                }
            },
        }
        try:
            response = httpx.post(
                "https://api.openai.com/v1/responses",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json=payload,
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict):
                raise TicketAssistantError
            output_text = body.get("output_text")
            if not isinstance(output_text, str):
                output = body.get("output", [])
                if not isinstance(output, list):
                    raise TicketAssistantError
                for item in output:
                    if not isinstance(item, dict):
                        raise TicketAssistantError
                    contents = item.get("content", [])
                    if not isinstance(contents, list):
                        raise TicketAssistantError
                    for content in contents:
                        if not isinstance(content, dict):
                            raise TicketAssistantError
                        if content.get("type") == "output_text":
                            output_text = content.get("text")
                            break
            if not isinstance(output_text, str):
                raise TicketAssistantError
            return TicketSuggestions.model_validate(json.loads(output_text))
        except (httpx.HTTPError, ValueError, TypeError, ValidationError, KeyError):
            raise TicketAssistantError from None
