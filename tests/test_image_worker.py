"""
tests.test_image_worker — Unit tests for the Image Worker node.

Role: Staff Quality & Reliability Engineer
Objective: Mathematically prove the image worker's mock execution mode.
"""

import os
import sys
from pathlib import Path

import pytest

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from CONTRACTS import MarketingContent
from logic.nodes.image_worker import image_worker_node


@pytest.mark.asyncio
async def test_image_worker_mock_mode():
    """Verify that image_worker_node writes mock image in mock mode."""
    # Force mock mode and customize media directory for testing
    os.environ["AGENCY_MOCK_LLM"] = "true"
    test_media_dir = "/tmp/test_media"
    os.environ["MEDIA_DIR"] = test_media_dir

    content = MarketingContent(
        caption="Mock Copywriting Caption",
        image_prompt="A stunning mock visual representation",
        aspect_ratio="9:16",
    )

    state = {
        "campaign_id": "test-campaign-123",
        "shadow_mode": True,
        "content": content,
        "stage": "reviewing",
    }

    # Run the node
    result = await image_worker_node(state)

    # Assertions
    assert "content" in result
    updated_content = result["content"]
    assert isinstance(updated_content, MarketingContent)
    assert updated_content.image_urls == ["/media/mock_image.png"]
    assert result["stage"] == "generating_image"
    assert any("Mock Mode" in line for line in result["logs"])

    # Verify physical file existence
    expected_file = Path(test_media_dir) / "mock_image.png"
    assert expected_file.exists(), f"Mock image was not created at {expected_file}"

    # Clean up test artifact
    try:
        expected_file.unlink()
        Path(test_media_dir).rmdir()
    except OSError:
        pass
