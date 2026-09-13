"""
Pipeline Orchestrator: Connects and coordinates the Catalog Agent, Art Agent,
and Liquid Coder Agent into an end-to-end dropshipping product lifecycle.
"""

import logging
import time
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from tools.shopify_client import ShopifyClient
from tools.image_generator import ImageGeneratorTool
from agents.catalog_agent import CatalogAgent, OptimizedCatalogProduct
from agents.art_agent import ArtAgent, ArtAssetOutput
from agents.liquid_coder_agent import LiquidCoderAgent, LiquidInjectionOutput

logger = logging.getLogger("DropshippingPipelineOrchestrator")


class PipelineExecutionReport(BaseModel):
    execution_time_sec: float
    shop_domain: str
    catalog_result: OptimizedCatalogProduct
    art_result: ArtAssetOutput
    frontend_result: LiquidInjectionOutput
    status: str = "COMPLETED_SUCCESSFULLY"


class DropshippingPipelineOrchestrator:
    """
    Multi-Agent Pipeline Orchestrator.
    Manages end-to-end synchronization across Catalog, Art, and Frontend agents.
    """

    def __init__(
        self,
        shopify_client: Optional[ShopifyClient] = None,
        image_tool: Optional[ImageGeneratorTool] = None,
    ):
        self.shopify = shopify_client or ShopifyClient()
        self.image_tool = image_tool or ImageGeneratorTool()

        # Initialize Agents
        self.catalog_agent = CatalogAgent(shopify_client=self.shopify)
        self.art_agent = ArtAgent(shopify_client=self.shopify, image_tool=self.image_tool)
        self.liquid_coder_agent = LiquidCoderAgent(shopify_client=self.shopify)

    async def run(self, raw_dropship_payload: Dict[str, Any]) -> PipelineExecutionReport:
        """
        Executes the entire multi-agent lifecycle pipeline.
        """
        start_time = time.time()
        logger.info(">>> Starting Dropshipping Multi-Agent Lifecycle Pipeline <<<")

        # Step 1: Catalog Agent
        logger.info("[Step 1/3] Ingesting and optimizing product catalog payload...")
        catalog_result: OptimizedCatalogProduct = await self.catalog_agent.process_payload(raw_dropship_payload)
        logger.info(f"✔ Catalog Agent completed: '{catalog_result.optimized_seo_title}'")

        # Step 2: Art Agent
        logger.info("[Step 2/3] Engineering visual prompts and uploading assets to Shopify CDN...")
        art_result: ArtAssetOutput = await self.art_agent.generate_and_upload_assets(catalog_result)
        logger.info(f"✔ Art Agent completed: {len(art_result.assets)} assets hosted on CDN")

        # Step 2.5: Attach generated media directly to Shopify product gallery
        if catalog_result.shopify_product_id and art_result.assets:
            media_urls = [a.cdn_url for a in art_result.assets if a.cdn_url]
            if media_urls:
                try:
                    await self.shopify.add_product_media(
                        product_id=catalog_result.shopify_product_id,
                        media_urls=media_urls,
                        alt_text=catalog_result.optimized_seo_title,
                    )
                    logger.info(f"✔ Attached {len(media_urls)} visual assets to Shopify product media gallery")
                except Exception as e:
                    logger.warning(f"Could not attach media to Shopify product gallery: {e}")

        # Step 3: Frontend Liquid Coder Agent
        logger.info("[Step 3/3] Manipulating Liquid theme templates and injecting assets...")
        frontend_result: LiquidInjectionOutput = await self.liquid_coder_agent.inject_theme_enhancements(
            product=catalog_result,
            art=art_result,
        )
        logger.info(f"✔ Frontend Liquid Coder Agent completed: Theme '{frontend_result.theme_name}' updated")


        duration = round(time.time() - start_time, 3)
        logger.info(f">>> Pipeline completed successfully in {duration}s <<<")

        return PipelineExecutionReport(
            execution_time_sec=duration,
            shop_domain=self.shopify.shop_domain,
            catalog_result=catalog_result,
            art_result=art_result,
            frontend_result=frontend_result,
            status="COMPLETED_SUCCESSFULLY",
        )
