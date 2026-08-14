"""AI Coach socrático con adaptador OpenAI, validación y fallo seguro."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
from time import monotonic
from typing import Any, Protocol


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "ai_coach.json"

FOCUS_LABELS = {
    "problem": "Definición del problema",
    "evidence": "Uso y valoración de evidencia",
    "ai_critique": "Análisis crítico de IA",
    "decision": "Justificación de decisiones",
}

FALLBACK_QUESTIONS = {
    "problem": "¿Qué parte del problema cambiaría si consideraras a la persona más afectada por esta decisión?",
    "evidence": "¿Qué información apoyaría tu afirmación y qué limitación tendría esa información?",
    "ai_critique": "¿Qué está dando por cierto la IA sin haberlo comprobado?",
    "decision": "¿Qué razón propia sostiene tu decisión y qué estás dispuesto a sacrificar?",
}


@dataclass(frozen=True)
class CoachOutput:
    focus_dimension: str
    question: str
    safety_triggered: bool


@dataclass(frozen=True)
class AdapterResponse:
    output: CoachOutput
    model: str
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(frozen=True)
class CoachResult:
    focus_dimension: str
    question: str
    safety_triggered: bool
    mode: str
    model: str
    policy_version: str
    prompt_version: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    fallback_reason: str = ""

    def to_record(self) -> dict[str, Any]:
        return asdict(self)


class AIAdapter(Protocol):
    def generate(self, *, context: dict[str, Any], focus_dimension: str, config: dict[str, Any]) -> AdapterResponse: ...


def load_coach_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if os.getenv("OPENAI_MODEL"):
        config["model"] = os.environ["OPENAI_MODEL"]
    return config


def select_focus(initial_responses: dict[str, str], answered_turns: list[dict[str, Any]]) -> str:
    """Elige una dimensión por reglas de completitud; no diagnostica al estudiante."""
    ordered = ("problem", "evidence", "ai_critique", "decision")
    used = [turn.get("focus_key") for turn in answered_turns]
    unused = [key for key in ordered if key not in used]
    candidates = unused or list(ordered)
    return min(candidates, key=lambda key: len(initial_responses.get(key, "").strip()))


def validate_non_resolutive(output: CoachOutput, expected_focus: str) -> str | None:
    question = output.question.strip()
    if output.focus_dimension != FOCUS_LABELS[expected_focus]:
        return "La dimensión de salida no coincide con el foco solicitado."
    if len(question) < 25 or len(question) > 240:
        return "La pregunta está fuera del límite de longitud."
    if question.count("?") != 1 or not question.endswith("?"):
        return "La salida debe contener exactamente una pregunta."
    if "\n" in question or re.search(r"(^|\s)(?:[-•]|\d+[.)])\s", question):
        return "La salida contiene una lista o más de una instrucción."
    forbidden = (
        "la respuesta es", "debes elegir", "deberías elegir", "te recomiendo",
        "la mejor opción", "la solución es", "escribe lo siguiente", "copia",
    )
    if any(phrase in question.casefold() for phrase in forbidden):
        return "La salida sugiere o entrega una respuesta."
    return None


class FakeAIAdapter:
    """Adaptador determinista para pruebas y demostraciones sin consumo de API."""

    def generate(self, *, context: dict[str, Any], focus_dimension: str, config: dict[str, Any]) -> AdapterResponse:
        return AdapterResponse(
            output=CoachOutput(FOCUS_LABELS[focus_dimension], FALLBACK_QUESTIONS[focus_dimension], False),
            model="fake-coach-v1",
        )


class OpenAIResponsesAdapter:
    """Adaptador del Responses API; la dependencia se importa sólo al usar IA real."""

    def __init__(self, api_key: str, timeout_seconds: int = 20) -> None:
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key, timeout=timeout_seconds, max_retries=1)

    def generate(self, *, context: dict[str, Any], focus_dimension: str, config: dict[str, Any]) -> AdapterResponse:
        from pydantic import BaseModel

        class StructuredCoachOutput(BaseModel):
            focus_dimension: str
            question: str
            safety_triggered: bool

        prompt_path = (ROOT / config["prompt_path"]).resolve()
        if ROOT not in prompt_path.parents:
            raise ValueError("La ruta del prompt debe permanecer dentro del proyecto.")
        instructions = prompt_path.read_text(encoding="utf-8")
        response = self.client.responses.parse(
            model=config["model"],
            instructions=instructions,
            input=json.dumps(context, ensure_ascii=False),
            text_format=StructuredCoachOutput,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise ValueError("La API no devolvió una salida estructurada utilizable.")
        usage = getattr(response, "usage", None)
        return AdapterResponse(
            output=CoachOutput(parsed.focus_dimension, parsed.question, parsed.safety_triggered),
            model=getattr(response, "model", config["model"]),
            input_tokens=int(getattr(usage, "input_tokens", 0) or 0),
            output_tokens=int(getattr(usage, "output_tokens", 0) or 0),
        )


def _api_key_from_runtime() -> str:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if key:
        return key
    try:
        import streamlit as st

        return str(st.secrets.get("OPENAI_API_KEY", "")).strip()
    except Exception:
        return ""


class CoachService:
    def __init__(self, config: dict[str, Any] | None = None, adapter: AIAdapter | None = None) -> None:
        self.config = config or load_coach_config()
        self.adapter = adapter

    def _adapter(self) -> tuple[AIAdapter, str, str]:
        if self.adapter is not None:
            return self.adapter, "injected", ""
        api_key = _api_key_from_runtime()
        if self.config.get("enabled") and self.config.get("provider") == "openai" and api_key:
            try:
                return OpenAIResponsesAdapter(api_key, int(self.config["timeout_seconds"])), "openai", ""
            except Exception as exc:
                return FakeAIAdapter(), "fallback", f"No fue posible inicializar el adaptador real: {type(exc).__name__}."
        return FakeAIAdapter(), "fallback", "No hay una clave de API configurada; se utilizó el banco pedagógico."

    def next_question(
        self,
        *,
        case: dict[str, Any],
        initial_responses: dict[str, str],
        answered_turns: list[dict[str, Any]],
    ) -> CoachResult:
        focus_key = select_focus(initial_responses, answered_turns)
        context = {
            "case": {
                "title": case.get("title", ""),
                "central_question": case.get("central_question", ""),
                "facts": case.get("facts", []),
            },
            "target_focus": FOCUS_LABELS[focus_key],
            "initial_excerpt": initial_responses.get(focus_key, ""),
            "previous_turns": [
                {"question": turn.get("question", ""), "student_response": turn.get("response", "")}
                for turn in answered_turns[-2:]
            ],
        }
        adapter, mode, adapter_reason = self._adapter()
        started = monotonic()
        reason = adapter_reason
        try:
            raw = adapter.generate(context=context, focus_dimension=focus_key, config=self.config)
            validation_error = validate_non_resolutive(raw.output, focus_key)
            if validation_error:
                raise ValueError(validation_error)
            output = raw.output
        except Exception as exc:
            if not self.config.get("fallback_enabled", True):
                raise
            mode = "fallback"
            reason = reason or f"Fallo o bloqueo de guardrail: {type(exc).__name__}."
            raw = AdapterResponse(
                output=CoachOutput(FOCUS_LABELS[focus_key], FALLBACK_QUESTIONS[focus_key], True),
                model=self.config.get("model", "unknown"),
            )
            output = raw.output
        return CoachResult(
            focus_dimension=output.focus_dimension,
            question=output.question.strip(),
            safety_triggered=output.safety_triggered,
            mode=mode,
            model=raw.model,
            policy_version=self.config["policy_version"],
            prompt_version=self.config["prompt_version"],
            latency_ms=round((monotonic() - started) * 1000),
            input_tokens=raw.input_tokens,
            output_tokens=raw.output_tokens,
            fallback_reason=reason,
        )
