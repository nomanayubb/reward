"""Survey provider adapter interface (docs/DRD.md §12)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class NormalizedSurvey:
    external_id: str
    title: str
    payout: Decimal
    description: str = ""
    category: str = ""
    country: str = ""
    language: str = ""
    device: str = ""
    estimated_minutes: int = 0
    qualification_rate: float | None = None
    daily_cap: int | None = None
    user_cap: int = 1
    expires_at: str | None = None
    raw: dict = field(default_factory=dict)


@dataclass
class NormalizedSurveyCompletion:
    external_completion_id: str
    user_identifier: str
    payout: Decimal
    survey_external_id: str = ""
    status: str = "approved"
    reason: str = ""
    raw: dict = field(default_factory=dict)


class SurveyProviderAdapter(ABC):
    code = "base"

    def __init__(self, provider, config: dict | None = None):
        self.provider = provider
        self.config = config if config is not None else (getattr(provider, "config", {}) or {})

    def get_surveys(self, user=None) -> list[NormalizedSurvey]:
        raise NotImplementedError

    def get_survey_url(self, survey, user, session) -> str:
        """Return the provider URL the user should open for this survey."""
        raise NotImplementedError

    def process_postback(self, payload: dict, headers: dict | None = None) -> NormalizedSurveyCompletion:
        raise NotImplementedError

    def validate_signature(self, payload: dict, headers: dict | None = None) -> bool:
        return True


def load_adapter(provider, config: dict | None = None) -> SurveyProviderAdapter:
    from django.utils.module_loading import import_string

    adapter_class = import_string(provider.adapter_path)
    return adapter_class(provider, config=config)
