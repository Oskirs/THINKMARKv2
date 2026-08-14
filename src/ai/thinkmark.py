"""Generación estructurada del borrador ThinkMark con fallo seguro local."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
from time import monotonic
from typing import Any, Protocol

from src.domain.thinkmark import THINKMARK_FIELDS, normalize_content, validate_content


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "thinkmark.json"


@dataclass(frozen=True)
class ThinkMarkResult:
    content: dict[str, str]
    mode: str
    model: str
    policy_version: str
    prompt_version: str
    latency_ms: int
    input_tokens: int = 0
    output_tokens: int = 0
    fallback_reason: str = ""

    def to_record(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AdapterResponse:
    content: dict[str, str]
    model: str
    input_tokens: int = 0
    output_tokens: int = 0


class ThinkMarkAdapter(Protocol):
    def generate(self, *, context: dict[str, Any], config: dict[str, Any]) -> AdapterResponse: ...


def load_thinkmark_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    model_override = os.getenv("OPENAI_THINKMARK_MODEL") or os.getenv("OPENAI_MODEL")
    if model_override:
        config["model"] = model_override
    return config


def build_thinkmark_context(state: dict[str, Any]) -> dict[str, Any]:
    """Expone únicamente evidencia expresada o validada durante el recorrido."""
    return {
        "initial": state.get("initial_responses", {}),
        "coach": [
            {"question": turn.get("question", ""), "student_response": turn.get("response", "")}
            for turn in state.get("coach_turns", [])
        ],
        "verification": (state.get("verifications") or [{}])[0],
        "challenge": (state.get("challenges") or [{}])[0],
        "decision": state.get("decision", {}),
        "reflection": state.get("final_responses", {}).get("responses", {}),
        "validated_delta": state.get("reasoning_evaluation", {}).get("calculation", {}),
    }


def local_draft(context: dict[str, Any]) -> dict[str, str]:
    initial = context.get("initial", {})
    verification = context.get("verification", {})
    challenge = context.get("challenge", {})
    decision = context.get("decision", {})
    reflection = context.get("reflection", {})
    source = verification.get("source_title", "la fuente registrada")
    assessment = verification.get("assessment", "fue valorada")
    def expressed(value: Any, absent: str) -> str:
        text = str(value or "").strip()
        return text if text else absent

    return normalize_content({
        "tm_initial_position": expressed(initial.get("decision"), "No se registró una posición inicial suficiente."),
        "tm_problem_reframed": expressed(reflection.get("problem"), "No se expresó una reformulación adicional del problema."),
        "tm_evidence_reviewed": f"Se revisó {source} para contrastar: {verification.get('claim', '')}",
        "tm_evidence_appraisal": f"La fuente {assessment} la afirmación. {verification.get('reliability_reason', '')} {verification.get('impact', '')}",
        "tm_ai_analysis": f"Se identificó esta limitación: {challenge.get('limitation', '')} El supuesto cuestionado fue: {challenge.get('assumption', '')}",
        "tm_final_decision": expressed(reflection.get("decision") or reflection.get("final_response"), "No se registró una decisión final suficiente."),
        "tm_reasoning_change": expressed(reflection.get("change"), "No se expresó un cambio específico; la postura puede haberse mantenido."),
        "tm_personal_contribution": expressed(
            reflection.get("human_contribution") or decision.get("tradeoff"),
            "No se expresó una contribución personal adicional en los campos disponibles.",
        ),
        "tm_remaining_limits": (
            f"Permanece esta incertidumbre: {reflection.get('uncertainty')} Siguiente paso: {reflection.get('next_step')}"
            if reflection.get("uncertainty") or reflection.get("next_step")
            else "No se expresaron límites o incertidumbres adicionales en los campos disponibles."
        ),
    })


class LocalThinkMarkAdapter:
    def generate(self, *, context: dict[str, Any], config: dict[str, Any]) -> AdapterResponse:
        return AdapterResponse(local_draft(context), "local-structured-v1")


class OpenAIThinkMarkAdapter:
    def __init__(self, api_key: str, timeout_seconds: int = 25) -> None:
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, timeout=timeout_seconds, max_retries=1)

    def generate(self, *, context: dict[str, Any], config: dict[str, Any]) -> AdapterResponse:
        from pydantic import BaseModel

        class StructuredThinkMark(BaseModel):
            tm_initial_position: str
            tm_problem_reframed: str
            tm_evidence_reviewed: str
            tm_evidence_appraisal: str
            tm_ai_analysis: str
            tm_final_decision: str
            tm_reasoning_change: str
            tm_personal_contribution: str
            tm_remaining_limits: str

        prompt_path = (ROOT / config["prompt_path"]).resolve()
        if ROOT not in prompt_path.parents:
            raise ValueError("La ruta del prompt debe permanecer dentro del proyecto.")
        response = self.client.responses.parse(
            model=config["model"],
            instructions=prompt_path.read_text(encoding="utf-8"),
            input=json.dumps(context, ensure_ascii=False),
            text_format=StructuredThinkMark,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise ValueError("La API no devolvió una ThinkMark estructurada utilizable.")
        usage = getattr(response, "usage", None)
        return AdapterResponse(
            content=parsed.model_dump(),
            model=getattr(response, "model", config["model"]),
            input_tokens=int(getattr(usage, "input_tokens", 0) or 0),
            output_tokens=int(getattr(usage, "output_tokens", 0) or 0),
        )


def _runtime_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if key:
        return key
    try:
        import streamlit as st
        return str(st.secrets.get("OPENAI_API_KEY", "")).strip()
    except Exception:
        return ""


class ThinkMarkService:
    def __init__(self, config: dict[str, Any] | None = None, adapter: ThinkMarkAdapter | None = None) -> None:
        self.config = config or load_thinkmark_config()
        self.adapter = adapter

    def generate(self, context: dict[str, Any]) -> ThinkMarkResult:
        mode = "injected" if self.adapter else "fallback"
        reason = ""
        adapter = self.adapter
        if adapter is None:
            api_key = _runtime_api_key()
            if self.config.get("enabled") and api_key:
                try:
                    adapter = OpenAIThinkMarkAdapter(api_key, int(self.config["timeout_seconds"]))
                    mode = "openai"
                except Exception as exc:
                    reason = f"No fue posible iniciar la integración: {type(exc).__name__}."
            if adapter is None:
                adapter = LocalThinkMarkAdapter()
                reason = reason or "No hay una clave de API configurada; se usó la síntesis local."

        started = monotonic()
        try:
            raw = adapter.generate(context=context, config=self.config)
            content = normalize_content(raw.content)
            if validate_content(content):
                raise ValueError("Salida incompleta")
        except Exception as exc:
            if not self.config.get("fallback_enabled", True):
                raise
            raw = LocalThinkMarkAdapter().generate(context=context, config=self.config)
            content = raw.content
            mode = "fallback"
            reason = reason or f"La propuesta externa no superó la validación: {type(exc).__name__}."
        return ThinkMarkResult(
            content=content,
            mode=mode,
            model=raw.model,
            policy_version=self.config["policy_version"],
            prompt_version=self.config["prompt_version"],
            latency_ms=round((monotonic() - started) * 1000),
            input_tokens=raw.input_tokens,
            output_tokens=raw.output_tokens,
            fallback_reason=reason,
        )
