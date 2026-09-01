from typing import Protocol

from .schemas import TicketSuggestions


class TicketAssistantError(Exception):
    """A safe, provider-independent AI failure."""


class TicketAssistant(Protocol):
    def suggest(self, *, title: str, description: str) -> TicketSuggestions: ...


class DisabledTicketAssistant:
    def suggest(self, *, title: str, description: str) -> TicketSuggestions:
        raise TicketAssistantError
