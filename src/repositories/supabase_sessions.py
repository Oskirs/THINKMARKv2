"""Repositorios Supabase con control de transición y concurrencia optimista."""

from __future__ import annotations

from typing import Any

from src.domain.activity_session import generate_session_code, validate_status_transition
from src.repositories.local_sessions import validate_record_transition


class SupabaseSessionRepository:
    def __init__(self, url: str, secret_key: str) -> None:
        from supabase import create_client
        self.client = create_client(url, secret_key)

    def _row(self, participant_id: str, activity_session_id: str = "") -> dict[str, Any] | None:
        query = self.client.table("thinkmark_sessions").select("record,revision").eq("participant_code", participant_id)
        if activity_session_id:
            query = query.eq("activity_session_id", activity_session_id)
        response = query.limit(1).execute()
        return response.data[0] if response.data else None

    def get(self, participant_id: str, activity_session_id: str = "") -> dict[str, Any] | None:
        row = self._row(participant_id, activity_session_id)
        return dict(row["record"]) if row else None

    def list_all(self) -> list[dict[str, Any]]:
        response = self.client.table("thinkmark_sessions").select("record").execute()
        return [dict(row["record"]) for row in (response.data or [])]

    def list_for_evaluator(self, user_id: str) -> list[dict[str, Any]]:
        assignments = (
            self.client.table("session_assignments")
            .select("session_id")
            .eq("user_id", user_id)
            .execute()
        )
        session_ids = [row["session_id"] for row in (assignments.data or [])]
        if not session_ids:
            return []
        response = self.client.table("thinkmark_sessions").select("record").in_("session_id", session_ids).execute()
        return [dict(row["record"]) for row in (response.data or [])]

    def get_activity_session(self, session_code: str) -> dict[str, Any] | None:
        response = self.client.table("activity_sessions").select("*").eq("session_code", session_code).limit(1).execute()
        return dict(response.data[0]) if response.data else None

    def create_activity_session(self, title: str, created_by: str, evaluator_id: str = "") -> dict[str, Any]:
        existing = self.client.table("activity_sessions").select("session_code").execute()
        code = generate_session_code([row["session_code"] for row in (existing.data or [])])
        response = self.client.table("activity_sessions").insert({
            "session_code": code,
            "title": title.strip(),
            "created_by": created_by,
        }).execute()
        record = dict(response.data[0])
        if evaluator_id:
            self.client.table("activity_session_assignments").insert({
                "activity_session_id": record["activity_session_id"],
                "user_id": evaluator_id,
                "assignment_role": "evaluator",
            }).execute()
        return record

    def list_activity_sessions_for_creator(self, user_id: str) -> list[dict[str, Any]]:
        response = self.client.table("activity_sessions").select("*").eq("created_by", user_id).order("created_at", desc=True).execute()
        return [dict(row) for row in (response.data or [])]

    def list_activity_sessions_for_evaluator(self, user_id: str) -> list[dict[str, Any]]:
        assignments = self.client.table("activity_session_assignments").select("activity_session_id").eq("user_id", user_id).execute()
        ids = [row["activity_session_id"] for row in (assignments.data or [])]
        if not ids:
            return []
        response = self.client.table("activity_sessions").select("*").in_("activity_session_id", ids).order("created_at", desc=True).execute()
        return [dict(row) for row in (response.data or [])]

    def list_participants(self, activity_session_id: str) -> list[dict[str, Any]]:
        response = self.client.table("thinkmark_sessions").select("record").eq("activity_session_id", activity_session_id).execute()
        return [dict(row["record"]) for row in (response.data or [])]

    def list_evaluators(self) -> list[dict[str, str]]:
        response = self.client.table("profiles").select("id,display_code").eq("role", "evaluator").eq("active", True).execute()
        return [{"user_id": str(row["id"]), "display_code": row["display_code"]} for row in (response.data or [])]

    def set_activity_session_status(self, session_code: str, status: str) -> None:
        current = self.get_activity_session(session_code)
        if not current:
            raise ValueError("La sesión no existe.")
        validate_status_transition(current["status"], status)
        self.client.table("activity_sessions").update({"status": status}).eq("session_code", session_code).execute()

    def save(self, record: dict[str, Any]) -> None:
        existing_row = self._row(record["participant_id"], record.get("activity_session_id", ""))
        existing = dict(existing_row["record"]) if existing_row else None
        validate_record_transition(existing, record)
        expected_revision = int(existing_row["revision"]) if existing_row else 0
        if record.get("activity_session_id"):
            self.client.rpc("save_thinkmark_session_v2", {
                "p_activity_session_id": record["activity_session_id"],
                "p_participant_code": record["participant_id"],
                "p_session_id": record["session_id"],
                "p_record": record,
                "p_expected_revision": expected_revision,
            }).execute()
        else:
            self.client.rpc("save_thinkmark_session", {
                "p_participant_code": record["participant_id"],
                "p_session_id": record["session_id"],
                "p_record": record,
                "p_expected_revision": expected_revision,
            }).execute()

    def audit_access(self, actor_id: str, actor_role: str, action: str, target_type: str, target_id: str = "") -> None:
        self.client.table("access_audit").insert({
            "actor_id": actor_id or None,
            "actor_role": actor_role,
            "action": action,
            "target_type": target_type,
            "target_id": target_id or None,
        }).execute()


class SupabaseLearningOpportunityRepository:
    def __init__(self, url: str, secret_key: str) -> None:
        from supabase import create_client
        self.client = create_client(url, secret_key)

    def get(self, activity_id: str) -> dict[str, Any] | None:
        response = (
            self.client.table("learning_opportunities")
            .select("record")
            .eq("activity_id", activity_id)
            .limit(1)
            .execute()
        )
        return dict(response.data[0]["record"]) if response.data else None

    def save_once(self, activity_id: str, record: dict[str, Any]) -> None:
        self.client.table("learning_opportunities").insert({
            "activity_id": activity_id,
            "record": record,
            "teacher_id": record.get("teacher_user_id"),
        }).execute()
