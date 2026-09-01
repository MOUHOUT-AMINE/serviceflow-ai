from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints
SuggestionText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class TicketSuggestions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: SuggestionText
    suggested_priority: Literal["low", "medium", "high"]
    recommended_action: SuggestionText
