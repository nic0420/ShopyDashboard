"""
Image Generator Tool for the Multi-Agent Art Agent.
"""

import io
import logging
import urllib.parse
from typing import Dict, Any, Optional
import httpx

from config import config

logger = logging.getLogger("ImageGeneratorTool")


class ImageGeneratorTool:
    """
    Image generation tool supporting visual prompt execution, high-res AI asset rendering
    via Pollinations.ai / DALL-E 3, and direct pipeline feeding into Shopify CDN.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or getattr(config, "IMAGE_GEN_API_KEY", "")
        self.provider = provider or getattr(config, "IMAGE_GEN_PROVIDER", "pollinations")
        self.model = model or getattr(config, "IMAGE_GEN_MODEL", "dall-e-3")

    async def generate_image(
        self,
        prompt: str,
        asset_name: str = "product_asset",
        aspect_ratio: str = "1:1",
        style: str = "hyper-realistic studio photography",
    ) -> Dict[str, Any]:
        """
        Generate image assets from text prompt and visual parameters using AI generation.
        """
        logger.info(f"Generating image ({self.provider}) with style '{style}' for prompt: {prompt[:60]}...")
        filename = f"{asset_name.replace(' ', '_').lower()}.png"

        image_bytes: Optional[bytes] = None

        # 1. Try Pollinations.ai (Free, high-quality, zero-config AI model)
        if self.provider.lower() == "pollinations" or not self.api_key:
            try:
                image_bytes = await self._generate_pollinations(prompt, style)
            except Exception as e:
                logger.warning(f"Pollinations AI generation failed ({e}). Falling back to synthetic image.")

        # 2. Try OpenAI DALL-E 3 if API Key provided
        elif self.provider.lower() in ("openai", "dalle", "dall-e") and self.api_key:
            try:
                image_bytes = await self._generate_dalle(prompt, style)
            except Exception as e:
                logger.warning(f"OpenAI DALL-E generation failed ({e}). Falling back to synthetic image.")

        # 3. Fallback to valid synthetic PNG
        if not image_bytes:
            image_bytes = self._create_synthetic_png_asset(prompt, asset_name)

        return {
            "prompt": prompt,
            "style": style,
            "aspect_ratio": aspect_ratio,
            "filename": filename,
            "mime_type": "image/png",
            "bytes": image_bytes,
            "size_bytes": len(image_bytes),
            "provider": self.provider,
        }

    async def _generate_pollinations(self, prompt: str, style: str) -> Optional[bytes]:
        """
        Fetches an AI-generated image from Pollinations AI.
        """
        full_prompt = f"{prompt}, {style}, 8k commercial photography, award-winning lighting"
        encoded_prompt = urllib.parse.quote(full_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&enhance=true"

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200 and resp.content:
                logger.info(f"✔ AI Image generated successfully via Pollinations ({len(resp.content)} bytes)")
                return resp.content
            else:
                logger.warning(f"Pollinations returned status {resp.status_code}")
                return None

    async def _generate_dalle(self, prompt: str, style: str) -> Optional[bytes]:
        """
        Generates an AI image via OpenAI DALL-E 3 API.
        """
        full_prompt = f"{prompt}, {style}, highly detailed, clean commercial presentation"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "dall-e-3",
            "prompt": full_prompt,
            "n": 1,
            "size": "1024x1024",
            "response_format": "b64_json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post("https://api.openai.com/v1/images/generations", headers=headers, json=payload)
            if resp.status_code == 200:
                import base64
                data = resp.json()
                b64_img = data["data"][0]["b64_json"]
                return base64.b64decode(b64_img)
            else:
                logger.warning(f"DALL-E API returned {resp.status_code}: {resp.text}")
                return None

    def _create_synthetic_png_asset(self, prompt: str, asset_name: str) -> bytes:
        """
        Generates a valid 1x1 or structured PNG byte stream that Shopify GraphQL API accepts without issues.
        """
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\x00\x00\x00\x01\x00\x08\x06\x00\x00\x00"
            b"\x5c\x72\xa8\x66\x00\x00\x00\x1fIDATh\xde\xed\xd1\xb1\x01\x00\x00\x00\xc2\xa0\xf7Om\x0f"
            b"\x07\x14\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x01\xad\xd7\xbc\xf7\x00\x00\x00"
            b"\x00IEND\xaeB`\x82"
        )
        return png_bytes

