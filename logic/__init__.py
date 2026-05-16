"""
logic — V3 LangGraph Orchestration Package.

Owns the graph definition, state schema, node wiring, and all
conditional routing logic for the Agency V3 multi-agent swarm.

Public API:
    build_v3_graph()  — compile the StateGraph with checkpointer
    V3GraphState      — annotated TypedDict for LangGraph reducers
"""

from logic.graph import build_v3_graph
from logic.state import V3GraphState

__all__ = [
    "build_v3_graph",
    "V3GraphState",
]
