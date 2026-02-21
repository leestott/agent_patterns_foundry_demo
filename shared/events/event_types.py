"""Event types emitted by instrumented agents and orchestrations."""

from enum import Enum


class EventType(str, Enum):
    AGENT_STARTED = "agent_started"
    AGENT_MESSAGE = "agent_message"
    TOOL_CALLED = "tool_called"
    TOOL_RESULT = "tool_result"
    HANDOFF = "handoff"
    AGENT_COMPLETED = "agent_completed"
    ERROR = "error"
