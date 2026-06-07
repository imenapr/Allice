"""
ALLICE — Agent State Machine
Tracks what the AI is currently doing and emits state changes.
"""

from enum import Enum
from PySide6.QtCore import QObject, Signal


class AgentState(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    CODING = "coding"
    EXECUTING = "executing"
    READING = "reading"
    ERROR = "error"


STATE_LABELS = {
    AgentState.IDLE: "Ready",
    AgentState.THINKING: "Thinking...",
    AgentState.CODING: "Writing code...",
    AgentState.EXECUTING: "Executing...",
    AgentState.READING: "Reading files...",
    AgentState.ERROR: "Error",
}

STATE_COLORS = {
    AgentState.IDLE: "#484f58",
    AgentState.THINKING: "#f59e0b",
    AgentState.CODING: "#7c3aed",
    AgentState.EXECUTING: "#22c55e",
    AgentState.READING: "#38bdf8",
    AgentState.ERROR: "#ef4444",
}


class Agent(QObject):
    state_changed = Signal(str, str)  # (state_name, label)
    token_received = Signal(str)
    response_complete = Signal(str)
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        self._state = AgentState.IDLE
        self.current_reply = ""

    @property
    def state(self) -> AgentState:
        return self._state

    def set_state(self, state: AgentState):
        self._state = state
        self.state_changed.emit(state.value, STATE_LABELS[state])

    def get_color(self) -> str:
        return STATE_COLORS[self._state]

    def begin_response(self):
        self.current_reply = ""
        self.set_state(AgentState.THINKING)

    def on_token(self, token: str):
        self.current_reply += token
        # Heuristic: switch to "coding" state when code block detected
        if "```" in self.current_reply and self._state == AgentState.THINKING:
            self.set_state(AgentState.CODING)
        self.token_received.emit(token)

    def on_done(self, full_reply: str):
        self.current_reply = full_reply
        self.set_state(AgentState.IDLE)
        self.response_complete.emit(full_reply)

    def on_error(self, message: str):
        self.set_state(AgentState.ERROR)
        self.error_occurred.emit(message)
