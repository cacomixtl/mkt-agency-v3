"""
logic.nodes.image_worker — Image Worker Node.

Generates campaign images via Gemini Imagen model or writes a placeholder image in mock mode.

Contract compliance:
  - Reads:   campaign_id (str), shadow_mode (bool), content (MarketingContent)
  - Writes:  content (MarketingContent), stage (CampaignStage), logs (list[str])
  - Stage produced: 'generating_image'
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any

from PIL import Image

from CONTRACTS import MarketingContent
from guardrails import validate_node_output

logger = logging.getLogger(__name__)


@validate_node_output
async def image_worker_node(state: dict[str, Any]) -> dict[str, Any]:
    """Image Worker — generates image for the campaign."""
    campaign_id = state.get("campaign_id", "unknown")
    shadow_mode = state.get("shadow_mode", True)
    content = state.get("content")

    if not content:
        logger.warning(
            "Image worker node called but content is missing in state. campaign=%s",
            campaign_id,
        )
        return {}

    logs_out: list[str] = []
    MEDIA_DIR = os.getenv("MEDIA_DIR", "/tmp/media")
    os.makedirs(MEDIA_DIR, exist_ok=True)

    is_mock = os.getenv("AGENCY_MOCK_LLM", "false").lower() == "true"

    try:
        if is_mock:
            logger.info(
                "Image Worker Mock Mode active  campaign=%s  stage=%s",
                campaign_id,
                "generating_image",
            )
            logs_out.append("[ImageWorker] Mock Mode: writing placeholder PNG")
            
            # Write a simple placeholder PNG using Pillow
            img = Image.new("RGB", (100, 100), color=(73, 109, 137))
            mock_image_path = os.path.join(MEDIA_DIR, "mock_image.png")
            img.save(mock_image_path)
            
            image_urls = ["/media/mock_image.png"]
            logs_out.append("[ImageWorker] Placeholder PNG written.")
        else:
            logger.info(
                "Image Worker invoking GenAI  campaign=%s  stage=%s",
                campaign_id,
                "generating_image",
            )
            logs_out.append("[ImageWorker] Invoking Google GenAI for image generation...")
            
            from google import genai
            from google.genai import types

            client = genai.Client()
            model_name = os.getenv("AGENCY_IMAGE_MODEL", "imagen-3.0-generate-002")

            aspect_ratio = content.aspect_ratio
            mapped_ratio = "3:4" if aspect_ratio == "4:5" else aspect_ratio

            response = client.models.generate_images(
                model=model_name,
                prompt=content.image_prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio=mapped_ratio
                )
            )

            generated_image = response.generated_images[0]
            image_bytes = generated_image.image.image_bytes

            filename = f"{campaign_id}_{uuid.uuid4().hex}.jpg"
            file_path = os.path.join(MEDIA_DIR, filename)

            with open(file_path, "wb") as f:
                f.write(image_bytes)

            image_urls = [f"/media/{filename}"]
            logs_out.append(f"[ImageWorker] Image generated: {filename}")

        updated_content = content.model_copy(update={"image_urls": image_urls})
        
        logger.info(
            "Image worker complete  campaign=%s  stage=%s",
            campaign_id,
            "generating_image",
        )

        return {
            "content": updated_content,
            "stage": "generating_image",
            "logs": logs_out,
        }

    except Exception as e:
        logger.error(
            "Image generation failed  campaign=%s  stage=%s  error=%s",
            campaign_id,
            "generating_image",
            str(e),
        )
        logs_out.append(f"[ImageWorker] Warning: Image generation failed: {str(e)}")
        
        # fallback returning content with image_urls = []
        updated_content = content.model_copy(update={"image_urls": []})
        return {
            "content": updated_content,
            "stage": "generating_image",
            "logs": logs_out,
        }
