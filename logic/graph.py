"""
logic.graph — V3 StateGraph Builder.

Pure wiring file.  Contains zero business logic — only imports
the state schema, node functions, routing logic, and assembles
the LangGraph StateGraph with edges, conditional routing, and
checkpointer.

Current topology (Supervisor Swarm):

    START → manager_node
                 │
                 ├── [conditional] ──→ creative_worker ──┐
                 ├── [conditional] ──→ judge_worker ─────┤
                 └── [conditional] ──→ wait_for_approval │
                                             │           │
                                       publisher_node    │
                                             │           │
    END ←────────────────────────────────────┘           │
      ↑                                                  │
      └──────────────────────────────────────────────────┘

The compiled graph is passed the AsyncPostgresSaver checkpointer
so that every super-step boundary is durably checkpointed to
PostgreSQL. The graph interrupts AFTER `wait_for_approval` to
provide the HITL Handshake.
"""

from __future__ import annotations

import logging

from langgraph.graph import END, StateGraph

from logic.nodes.approval import approval_node
from logic.nodes.creative import creative_worker_node
from logic.nodes.judge import judge_worker_node
from logic.nodes.manager import manager_node
from logic.nodes.publisher import publisher_node
from logic.routing import supervisor_router
from logic.state import V3GraphState

logger = logging.getLogger(__name__)


def build_v3_graph(checkpointer=None) -> StateGraph:
    """Compile the Agency V3 StateGraph.

    Args:
        checkpointer: A LangGraph-compatible checkpointer. Pass
                      ``None`` for in-memory-only (unit tests).

    Returns:
        A compiled LangGraph ``StateGraph`` ready for
        ``.ainvoke()`` or ``.astream_events()``.
    """
    graph = StateGraph(V3GraphState)

    # ── Nodes ──
    graph.add_node("manager_node", manager_node)
    graph.add_node("creative_worker", creative_worker_node)
    graph.add_node("judge_worker", judge_worker_node)
    graph.add_node("wait_for_approval", approval_node)
    graph.add_node("publisher_node", publisher_node)

    # ── Edges ──
    graph.set_entry_point("manager_node")

    # Workers always return to the Supervisor
    graph.add_edge("creative_worker", "manager_node")
    graph.add_edge("judge_worker", "manager_node")

    # Supervisor conditional routing
    graph.add_conditional_edges(
        "manager_node",
        supervisor_router,
        {
            "creative_worker": "creative_worker",
            "judge_worker": "judge_worker",
            "wait_for_approval": "wait_for_approval",
        },
    )

    # HITL gate feeds publisher; publisher terminates to END
    graph.add_edge("wait_for_approval", "publisher_node")
    graph.add_edge("publisher_node", END)

    # ── Compile ──
    compiled = graph.compile(
        checkpointer=checkpointer,
        interrupt_after=["wait_for_approval"],
    )

    logger.info(
        "V3 Supervisor graph compiled checkpointer=%s",
        type(checkpointer).__name__ if checkpointer else "None",
    )

    return compiled
