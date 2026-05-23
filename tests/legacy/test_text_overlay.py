import os
from pathlib import Path

from PIL import Image

# Setup dummy environment variables for config
os.environ["GOOGLE_API_KEY"] = "dummy"
os.environ["GEMINI_MODEL"] = "gemini-2.5-flash"

from app.services.image_gen.service import image_gen_service


def test_overlay():
    # 1. Create a dummy 9:16 image
    test_img_path = Path("test_story.jpg")
    img = Image.new("RGB", (1080, 1920), color="salmon")
    img.save(test_img_path)

    # 2. Add text overlay
    long_caption = (
        "¡Oferta especial de primavera! 🌸\n\n"
        "Aprovecha nuestros nuevos descuentos en toda la tienda. "
        "Ven y conoce nuestra nueva colección de temporada."
    )

    print("Applying overlay...")
    image_gen_service.add_text_overlay_to_image(test_img_path, long_caption)

    # 3. Check if file exists and has size
    assert test_img_path.exists()
    assert test_img_path.stat().st_size > 0
    print(f"Success! Image saved to {test_img_path.absolute()}")

    # Cleanup
    test_img_path.unlink()


if __name__ == "__main__":
    test_overlay()
