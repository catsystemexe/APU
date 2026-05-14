from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class APURequest:
    message: str
    state: Dict[str, Any] = field(default_factory=dict)


@dataclass
class APUPipelineMeta:
    intent: Optional[str] = None

    signals: List[Dict[str, Any]] = field(default_factory=list)

    input_quality: Dict[str, Any] = field(default_factory=dict)

    blocks: List[Dict[str, Any]] = field(default_factory=list)
    profiles: List[Dict[str, Any]] = field(default_factory=list)
    zones: List[Dict[str, Any]] = field(default_factory=list)

    interventions: List[Dict[str, Any]] = field(default_factory=list)

    didactic_filter: Dict[str, Any] = field(default_factory=dict)
    validation: Dict[str, Any] = field(default_factory=dict)

    output_mode: Optional[str] = None
    confidence: str = "LOW"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "signals": self.signals,
            "input_quality": self.input_quality,
            "blocks": self.blocks,
            "profiles": self.profiles,
            "zones": self.zones,
            "interventions": self.interventions,
            "didactic_filter": self.didactic_filter,
            "validation": self.validation,
            "output_mode": self.output_mode,
            "confidence": self.confidence,
        }


@dataclass
class APUPipelineResult:
    system_context: str
    user_message: str
    meta: APUPipelineMeta
