from __future__ import annotations

from typing import Literal, Optional, overload

from injector import Binder, Injector, Module, inject, provider

from taskweaver.config.module_config import ModuleConfig

from ..session import Session
from ..utils import create_id
from .session_store import InMemorySessionStore, SessionStore


class SessionManager:
    @inject
    def __init__(self, session_store: SessionStore, injector: Injector) -> None:
        self.session_store: SessionStore = session_store
        self.injector: Injector = injector

    def get_session(
        self,
        session_id: Optional[str] = None,
        prev_round_id: Optional[str] = None,
    ) -> Session:
        """get session from session store, if session_id is None, create a new session"""
        if session_id is None:
            assert prev_round_id is None
            session_id = create_id()
            return self._get_session_from_store(session_id, True)

        current_session = self._get_session_from_store(session_id, False)

        if current_session is None:
            raise Exception("session id not found")

        # if current_session.prev_round_id == prev_round_id or prev_round_id is None:
        #     return current_session

        # # TODO: create forked session from existing session for resubmission, modification, etc.
        # raise Exception(
        #     "currently only support continuing session in the last round: "
        #     f" session id {current_session.session_id}, prev round id {current_session.prev_round_id}",
        # )
        return current_session

    def update_session(self, session: Session) -> None:
        """update session in session store"""
        self.session_store.set_session(session.session_id, session)

    def stop_session(self, session_id: str) -> None:
        """stop session in session store"""
        session = self._get_session_from_store(session_id, False)
        if session is not None:
            session.stop()
            self.session_store.remove_session(session_id)

    def stop_all_sessions(self) -> None:
        session_ids = self.session_store.list_all_session_ids()
        for session_id in session_ids:
            self.stop_session(session_id)

    @overload
    def _get_session_from_store(
        self,
        session_id: str,
        create_new: Literal[False],
    ) -> Optional[Session]:
        ...

    @overload
    def _get_session_from_store(
        self,
        session_id: str,
        create_new: Literal[True],
    ) -> Session:
        ...

    def _get_session_from_store(
        self,
        session_id: str,
        create_new: bool = False,
    ) -> Session | None:
        if self.session_store.has_session(session_id):
            return self.session_store.get_session(session_id)
        else:
            if create_new:
                new_session = self.injector.create_object(
                    Session,
                    {"session_id": session_id},
                )
                self.session_store.set_session(session_id, new_session)
                return new_session
            return None


class SessionManagerConfig(ModuleConfig):
    def _configure(self):
        self._set_name("session_manager")
        self.session_store_type = self._get_enum(
            "store_type",
            ["in_memory"],
            "in_memory",
        )


class SessionManagerModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(SessionManager, to=SessionManager)

    @provider
    def provide_session_store(self, config: SessionManagerConfig) -> SessionStore:
        if config.session_store_type == "in_memory":
            return InMemorySessionStore()
        raise Exception(f"unknown session store type {config.session_store_type}")
