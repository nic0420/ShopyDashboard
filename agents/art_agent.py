"""
Art Agent: Responsible for visual prompt engineering, image generation,
and uploading assets to the Shopify CDN.
"""

import logging
from typing import Any, Dict, List
from pydantic import BaseModel, Field

from tools.shopify_client import ShopifyClient
from tools.image_generator import ImageGeneratorTool
from agents.catalog_agent import OptimizedCatalogProduct

logger = logging.getLogger("ArtAgent")


class GeneratedAsset(BaseModel):
    asset_type: str = Field(..., description="E.g., hero_product, lifestyle_scene, infographic_feature")
    prompt: str = Field(..., description="Engineered generative prompt")
    filename: str
    cdn_url: str
    shopify_file_id: str


class ArtAssetOutput(BaseModel):
    product_title: str
    assets: List[GeneratedAsset]
    primary_cdn_url: str
    gallery_cdn_urls: List[str]


class ArtAgent:
    """
    Agent responsible for translating product concepts into high-converting visual assets,
    calling image generation tools, and securing hosted URLs on Shopify CDN.
    """

    def __init__(self, shopify_client: ShopifyClient, image_tool: ImageGeneratorTool):
        self.shopify = shopify_client
        self.image_tool = image_tool

    def engineer_prompts(self, product: OptimizedCatalogProduct) -> List[Dict[str, str]]:
        """
        Creates a set of diverse, high-converting commercial photography prompts.
        """
        title = product.optimized_seo_title
        category = product.product_type
        hook = product.hook

        prompts = [
            {
                "type": "hero_studio",
                "name": f"{product.handle}_hero_studio",
                "prompt": (
                    f"Award-winning commercial product photography of {title}. "
                    f"Clean minimalist studio setting, softbox lighting, 8k resolution, photorealistic, "
                    f"subtle luxury gradient background, crisp details, zero artifacts."
                ),
                "aspect_ratio": "1:1",
                "style": "clean studio luxury commercial",
            },
            {
                "type": "lifestyle_context",
                "name": f"{product.handle}_lifestyle",
                "prompt": (
                    f"Realistic cinematic lifestyle shot showcasing {title} in active use. "
                    f"Natural daylight, modern aesthetic interior, depth of field bokeh, "
                    f"premium lifestyle photography, authentic composition."
                ),
                "aspect_ratio": "1:1",
                "style": "authentic cinematic lifestyle",
            },
            {
                "type": "feature_infographic",
                "name": f"{product.handle}_features_callout",
                "prompt": (
                    f"Isometric 3D product render of {title} highlighting internal mechanics and durability. "
                    f"High-tech futuristic clean aesthetics, neon cyan subtle accent glow, 4k ultra-crisp render."
                ),
                "aspect_ratio": "1:1",
                "style": "3d high-tech render",
            },
        ]
        return prompts

    async def generate_and_upload_assets(self, product: OptimizedCatalogProduct) -> ArtAssetOutput:
        """
        Orchestrates prompt generation, image synthesis, and Shopify CDN upload.
        """
        logger.info(f"Art Agent starting visual synthesis for product: {product.optimized_seo_title}")

        prompt_configs = self.engineer_prompts(product)
        uploaded_assets: List[GeneratedAsset] = []

        for config in prompt_configs:
            # 1. Generate image using ImageGeneratorTool
            img_result = await self.image_tool.generate_image(
                prompt=config["prompt"],
                asset_name=config["name"],
                aspect_ratio=config["aspect_ratio"],
                style=config["style"],
            )

            # 2. Upload asset directly to Shopify CDN
            upload_result = await self.shopify.upload_file_to_cdn(
                file_name=img_result["filename"],
                file_content=img_result["bytes"],
                mime_type=img_result["mime_type"],
                alt_text=f"{product.optimized_seo_title} - {config['type']}",
            )

            cdn_url = upload_result.get("url", "")
            file_id = upload_result.get("file_id", "")

            uploaded_assets.append(
                GeneratedAsset(
                    asset_type=config["type"],
                    prompt=config["prompt"],
                    filename=img_result["filename"],
                    cdn_url=cdn_url,
                    shopify_file_id=file_id,
                )
            )
            logger.info(f"Asset [{config['type']}] uploaded to CDN: {cdn_url}")

        primary_cdn = uploaded_assets[0].cdn_url if uploaded_assets else ""
        gallery_cdns = [a.cdn_url for a in uploaded_assets[1:]]

        return ArtAssetOutput(
            product_title=product.optimized_seo_title,
            assets=uploaded_assets,
            primary_cdn_url=primary_cdn,
            gallery_cdn_urls=gallery_cdns,
        )
