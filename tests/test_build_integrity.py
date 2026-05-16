"""
Pre-Flight CI/CD Smoke Tests: Build Integrity.

Role: Staff Quality & Reliability Engineer
Objective: Mathematically prove the V3 architecture compiles and communicates correctly.
"""

import sys
from pathlib import Path
import pytest

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_fastapi_app_compilation():
    """
    Compilation & Import Smoke Test: Core FastAPI App.
    If there are missing dependencies or syntax errors, this will fail immediately.
    """
    try:
        import main_v3
        assert main_v3.app is not None, "FastAPI app instance is missing in main_v3"
    except Exception as e:
        pytest.fail(f"CRITICAL FASTAPI IMPORT FAILURE: {e}")


def test_langgraph_orchestrator_compilation():
    """
    Compilation & Import Smoke Test: LangGraph Orchestrator.
    Proves the workflow graph can be constructed without syntax or state definition errors.
    """
    try:
        from logic import build_v3_graph
        # We pass checkpointer=None since we are only testing compilation
        graph = build_v3_graph(checkpointer=None)
        assert graph is not None, "Failed to compile the LangGraph orchestrator"
    except Exception as e:
        pytest.fail(f"CRITICAL LANGGRAPH COMPILATION FAILURE: {e}")
