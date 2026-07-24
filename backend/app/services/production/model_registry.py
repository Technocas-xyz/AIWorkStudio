"""Model Registry - plugin architecture for AI model providers."""

import os
from typing import Optional
from dotenv import load_dotenv

_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv(os.path.join(_root, ".env"))

# Registry of available AI model adapters
REGISTERED_MODELS = {}


def register_model(name: str, adapter_class):
    """Register an AI model adapter."""
    REGISTERED_MODELS[name] = adapter_class


def get_model_adapter(name: str):
    """Get an instantiated model adapter by name."""
    adapter_class = REGISTERED_MODELS.get(name)
    if not adapter_class:
        raise ValueError(f"Model '{name}' is not registered. Available: {list(REGISTERED_MODELS.keys())}")
    return adapter_class()


def list_models() -> list:
    """List all registered models with their capabilities."""
    models = []
    for name, cls in REGISTERED_MODELS.items():
        adapter = cls()
        models.append({
            "name": name,
            "display_name": adapter.display_name,
            "provider": adapter.provider,
            "is_available": adapter.is_available(),
            "supported_modes": adapter.supported_modes,
            "max_resolution": adapter.max_resolution,
        })
    return models


class BaseModelAdapter:
    """Base class for AI model adapters."""
    name: str = "base"
    display_name: str = "Base Model"
    provider: str = "unknown"
    supported_modes: list = []
    max_resolution: int = 4096

    def is_available(self) -> bool:
        return False

    async def generate(self, prompt: str, reference_image: Optional[bytes] = None,
                       width: int = 1024, height: int = 1024, **kwargs) -> Optional[bytes]:
        raise NotImplementedError


class GPTImageAdapter(BaseModelAdapter):
    """OpenAI GPT Image generation adapter."""
    name = "gpt_image"
    display_name = "GPT Image"
    provider = "OpenAI"
    supported_modes = ["reconstruction", "enhancement", "upscaling", "background_cleanup", "edge_refinement", "production_cleanup"]
    max_resolution = 4096

    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key != "your-openai-api-key-here")

    async def generate(self, prompt: str, reference_image: Optional[bytes] = None,
                       width: int = 1024, height: int = 1024, **kwargs) -> Optional[bytes]:
        """Generate image using OpenAI's image API."""
        if not self.is_available():
            raise RuntimeError("OpenAI API key not configured")

        from openai import OpenAI
        import base64

        client = OpenAI(api_key=self.api_key)

        try:
            if reference_image:
                # Edit mode - use reference image with proper filename for MIME detection
                import io
                # Detect format from bytes
                img_format = "png"
                if reference_image[:3] == b'\xff\xd8\xff':
                    img_format = "jpeg"
                elif reference_image[:4] == b'RIFF':
                    img_format = "webp"

                # Convert to PNG if needed (safest format for the API)
                from PIL import Image
                pil_img = Image.open(io.BytesIO(reference_image))
                png_buf = io.BytesIO()
                pil_img.save(png_buf, format="PNG")
                pil_img.close()
                png_buf.seek(0)
                png_buf.name = "image.png"

                result = client.images.edit(
                    model="gpt-image-1",
                    image=png_buf,
                    prompt=prompt,
                )
                # Download the image from URL
                if result.data and result.data[0].url:
                    import httpx
                    img_response = httpx.get(result.data[0].url)
                    return img_response.content
                elif result.data and result.data[0].b64_json:
                    return base64.b64decode(result.data[0].b64_json)
            else:
                # Generate mode
                result = client.images.generate(
                    model="gpt-image-1",
                    prompt=prompt,
                    size="1024x1024",
                    n=1,
                )
                if result.data and result.data[0].url:
                    import httpx
                    img_response = httpx.get(result.data[0].url)
                    return img_response.content
                elif result.data and result.data[0].b64_json:
                    return base64.b64decode(result.data[0].b64_json)

            return None

        except Exception as e:
            raise RuntimeError(f"GPT Image generation failed: {str(e)}")


class FluxAdapter(BaseModelAdapter):
    """Flux model adapter (placeholder for API integration)."""
    name = "flux"
    display_name = "Flux"
    provider = "Black Forest Labs"
    supported_modes = ["reconstruction", "enhancement", "upscaling"]
    max_resolution = 2048

    def __init__(self):
        self.api_key = os.environ.get("FLUX_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def generate(self, prompt: str, reference_image: Optional[bytes] = None,
                       width: int = 1024, height: int = 1024, **kwargs) -> Optional[bytes]:
        raise RuntimeError("Flux API integration pending - configure FLUX_API_KEY")


class NanoBananaAdapter(BaseModelAdapter):
    """Nano Banana model adapter (placeholder)."""
    name = "nano_banana"
    display_name = "Nano Banana"
    provider = "Banana.dev"
    supported_modes = ["enhancement", "upscaling"]
    max_resolution = 2048

    def __init__(self):
        self.api_key = os.environ.get("BANANA_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def generate(self, prompt: str, reference_image: Optional[bytes] = None,
                       width: int = 1024, height: int = 1024, **kwargs) -> Optional[bytes]:
        raise RuntimeError("Nano Banana API integration pending - configure BANANA_API_KEY")


# Register all models
register_model("gpt_image", GPTImageAdapter)
register_model("flux", FluxAdapter)
register_model("nano_banana", NanoBananaAdapter)
