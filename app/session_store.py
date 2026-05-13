import json
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from uuid import uuid4

from app.schemas import ChatTurn, SessionDetail, SessionRecord


def derive_title(question: str) -> str:
    compact = " ".join(question.strip().split())
    if not compact:
        return "新会话"
    return compact[:30] + ("..." if len(compact) > 30 else "")


class SessionStore:
    def __init__(self, sessions_path: str):
        self.sessions_path = Path(sessions_path)
        self.sessions_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = Lock()

    def list_sessions(self) -> list[SessionRecord]:
        sessions = [SessionDetail.model_validate(item) for item in self._read_json()]
        sessions.sort(key=lambda item: item.updated_at, reverse=True)
        return [self._to_record(item) for item in sessions]

    def create_session(self, title: str | None = None) -> SessionRecord:
        now = datetime.now(UTC)
        session = SessionDetail(
            id=uuid4().hex,
            title=title or "新会话",
            created_at=now,
            updated_at=now,
            messages=[],
            last_message=None,
            turn_count=0,
        )
        with self.lock:
            sessions = self._read_json()
            sessions.append(session.model_dump(mode="json"))
            self._write_json(sessions)
        return self._to_record(session)

    def get_session(self, session_id: str) -> SessionDetail | None:
        for item in self._read_json():
            if item["id"] == session_id:
                return SessionDetail.model_validate(item)
        return None

    def append_exchange(self, session_id: str, question: str, answer: str) -> SessionDetail | None:
        with self.lock:
            sessions = self._read_json()
            for index, item in enumerate(sessions):
                if item["id"] != session_id:
                    continue

                session = SessionDetail.model_validate(item)
                if not session.messages and session.title == "新会话":
                    session.title = derive_title(question)
                session.messages.extend(
                    [
                        ChatTurn(role="user", content=question),
                        ChatTurn(role="assistant", content=answer),
                    ]
                )
                session.updated_at = datetime.now(UTC)
                session.last_message = answer[:120]
                session.turn_count = len(session.messages)
                sessions[index] = session.model_dump(mode="json")
                self._write_json(sessions)
                return session
        return None

    def delete_session(self, session_id: str) -> bool:
        with self.lock:
            sessions = self._read_json()
            kept = [item for item in sessions if item["id"] != session_id]
            if len(kept) == len(sessions):
                return False
            self._write_json(kept)
        return True

    def ensure_session(self, session_id: str | None, fallback_history: list[ChatTurn]) -> SessionDetail:
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session
        record = self.create_session()
        return SessionDetail(**record.model_dump(), messages=fallback_history)

    def seed_history(self, session_id: str, history: list[ChatTurn]) -> SessionDetail | None:
        with self.lock:
            sessions = self._read_json()
            for index, item in enumerate(sessions):
                if item["id"] != session_id:
                    continue
                session = SessionDetail.model_validate(item)
                if not session.messages and history:
                    session.messages = history
                    session.turn_count = len(history)
                    session.updated_at = datetime.now(UTC)
                    last_message = history[-1].content if history else None
                    session.last_message = last_message[:120] if last_message else None
                    sessions[index] = session.model_dump(mode="json")
                    self._write_json(sessions)
                return session
        return None

    @staticmethod
    def _to_record(session: SessionDetail) -> SessionRecord:
        return SessionRecord(
            id=session.id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            last_message=session.last_message,
            turn_count=session.turn_count,
        )

    def _read_json(self) -> list[dict]:
        if not self.sessions_path.exists():
            return []
        return json.loads(self.sessions_path.read_text(encoding="utf-8"))

    def _write_json(self, value: list[dict]) -> None:
        self.sessions_path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
