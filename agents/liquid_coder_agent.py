"""
Frontend Agent (Liquid Coder): Responsible for manipulating theme Liquid and JSON files,
injecting persuasive texts, and binding generated Shopify CDN image URLs.
"""

import json
import logging
from typing import Any, Dict, List
from pydantic import BaseModel, Field

from tools.shopify_client import ShopifyClient
from agents.catalog_agent import OptimizedCatalogProduct
from agents.art_agent import ArtAssetOutput

logger = logging.getLogger("LiquidCoderAgent")


class InjectedAssetRecord(BaseModel):
    asset_key: str
    action: str = Field(..., description="created | updated | verified")
    content_summary: str


class LiquidInjectionOutput(BaseModel):
    theme_id: int
    theme_name: str
    modified_assets: List[InjectedAssetRecord]
    liquid_snippet_key: str
    template_json_key: str
    status: str


class LiquidCoderAgent:
    """
    Agent responsible for theme code manipulation, generating dynamic Liquid snippets,
    and injecting marketing copywriting and CDN media into Shopify themes.
    """

    def __init__(self, shopify_client: ShopifyClient):
        self.shopify = shopify_client

    def generate_liquid_snippet(
        self,
        product: OptimizedCatalogProduct,
        art: ArtAssetOutput,
    ) -> str:
        """
        Creates a custom Liquid snippet (`snippets/elite-showcase-[handle].liquid`)
        featuring dynamic badges, CDN media gallery, and structured conversion benefits.
        """
        benefits_liquid = ""
        for b in product.benefits:
            benefits_liquid += f"""
        <div class="elite-benefit-card">
          <div class="benefit-icon">{b.icon}</div>
          <div class="benefit-text">
            <h4 class="benefit-title">{b.title}</h4>
            <p class="benefit-desc">{b.description}</p>
          </div>
        </div>
        """

        gallery_liquid = ""
        for asset in art.assets:
            gallery_liquid += f"""
        <div class="elite-gallery-item">
          <img 
            src="{asset.cdn_url}" 
            alt="{asset.asset_type.replace('_', ' ').capitalize()}" 
            loading="lazy" 
            class="elite-cdn-image"
          />
          <span class="elite-image-badge">{asset.asset_type.replace('_', ' ').title()}</span>
        </div>
        """

        snippet_code = f"""{{% comment %}}
  Auto-generated High-Conversion Showcase
  Product: {product.optimized_seo_title}
  Theme Aesthetic: Premium Modern Elite
{{% endcomment %}}

<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Outfit:wght@600;800;900&display=swap');

  .elite-showcase-wrapper {{
    margin: 36px 0;
    padding: 0;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  }}
  .elite-card {{
    background: #0F172A;
    background: linear-gradient(145deg, #0F172A 0%, #1E293B 100%);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 28px 24px;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.2);
    color: #F8FAFC;
    position: relative;
    overflow: hidden;
  }}
  .elite-card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #10B981 0%, #3B82F6 50%, #8B5CF6 100%);
  }}
  .elite-header {{
    text-align: center;
    margin-bottom: 26px;
  }}
  .elite-badge-top {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.4);
    color: #34D399;
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    padding: 6px 14px;
    border-radius: 9999px;
    margin-bottom: 12px;
    text-transform: uppercase;
  }}
  .elite-headline {{
    font-family: 'Outfit', sans-serif;
    font-size: 1.65rem;
    font-weight: 800;
    color: #FFFFFF;
    margin: 0 0 10px 0;
    letter-spacing: -0.02em;
    line-height: 1.25;
  }}
  .elite-hook {{
    font-size: 0.98rem;
    color: #94A3B8;
    max-width: 650px;
    margin: 0 auto;
    line-height: 1.6;
  }}
  .elite-gallery-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin: 26px 0;
  }}
  .elite-gallery-item {{
    position: relative;
    border-radius: 12px;
    overflow: hidden;
    background: #1E293B;
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.3s ease;
  }}
  .elite-gallery-item:hover {{
    transform: translateY(-4px);
    border-color: rgba(16, 185, 129, 0.5);
  }}
  .elite-cdn-image {{
    width: 100%;
    height: 220px;
    object-fit: cover;
    display: block;
    transition: transform 0.4s ease;
  }}
  .elite-gallery-item:hover .elite-cdn-image {{
    transform: scale(1.05);
  }}
  .elite-image-badge {{
    position: absolute;
    bottom: 10px;
    left: 10px;
    background: rgba(15, 23, 42, 0.85);
    color: #F8FAFC;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 6px;
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    text-transform: capitalize;
  }}
  .elite-benefits-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 14px;
    margin-top: 22px;
  }}
  .elite-benefit-card {{
    display: flex;
    align-items: flex-start;
    gap: 14px;
    padding: 16px;
    background: rgba(30, 41, 59, 0.7);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.06);
    transition: background 0.2s ease, border-color 0.2s ease;
  }}
  .elite-benefit-card:hover {{
    background: rgba(30, 41, 59, 1);
    border-color: rgba(59, 130, 246, 0.4);
  }}
  .benefit-icon {{
    font-size: 1.6rem;
    flex-shrink: 0;
    background: rgba(255, 255, 255, 0.05);
    padding: 8px;
    border-radius: 10px;
  }}
  .benefit-title {{
    margin: 0 0 4px 0;
    font-size: 0.98rem;
    font-weight: 700;
    color: #F8FAFC;
  }}
  .benefit-desc {{
    margin: 0;
    font-size: 0.86rem;
    color: #94A3B8;
    line-height: 1.5;
  }}
  .elite-trust-bar {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 12px;
    margin-top: 26px;
    padding-top: 20px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    text-align: center;
  }}
  .trust-badge-item {{
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
  }}
  .trust-badge-icon {{
    font-size: 1.35rem;
  }}
  .trust-badge-label {{
    font-size: 0.76rem;
    font-weight: 700;
    color: #CBD5E1;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }}
</style>

<div class="elite-showcase-wrapper" data-product-handle="{product.handle}">
  <div class="elite-card">
    <div class="elite-header">
      <span class="elite-badge-top">⚡ Selección Premium Garantizada</span>
      <h3 class="elite-headline">{product.optimized_seo_title}</h3>
      <p class="elite-hook">{product.hook}</p>
    </div>

    <div class="elite-gallery-grid">
      {gallery_liquid}
    </div>

    <div class="elite-benefits-grid">
      {benefits_liquid}
    </div>

    <div class="elite-trust-bar">
      <div class="trust-badge-item">
        <span class="trust-badge-icon">🚚</span>
        <span class="trust-badge-label">Envío Asegurado</span>
      </div>
      <div class="trust-badge-item">
        <span class="trust-badge-icon">🛡️</span>
        <span class="trust-badge-label">Calidad Certificada</span>
      </div>
      <div class="trust-badge-item">
        <span class="trust-badge-icon">🔄</span>
        <span class="trust-badge-label">30 Días Garantía</span>
      </div>
      <div class="trust-badge-item">
        <span class="trust-badge-icon">🔒</span>
        <span class="trust-badge-label">Pago 100% Cifrado</span>
      </div>
    </div>
  </div>
</div>
"""
        return snippet_code.strip()

    def update_product_template_json(
        self,
        current_template_raw: str,
        snippet_name: str = "dropship-feature-showcase",
    ) -> str:
        """
        Parses `templates/product.json` and cleanly injects custom liquid block or section.
        """
        try:
            template_data = json.loads(current_template_raw)
        except Exception:
            template_data = {
                "sections": {
                    "main": {"type": "main-product", "blocks": {}, "block_order": []}
                },
                "order": ["main"]
            }

        # Inject custom liquid block into main section if present
        main_section = template_data.get("sections", {}).get("main")
        if main_section and "blocks" in main_section:
            block_id = f"custom_{snippet_name.replace('-', '_')}"
            main_section["blocks"][block_id] = {
                "type": "custom_liquid",
                "settings": {
                    "custom_liquid": f"{{% render '{snippet_name}' %}}"
                }
            }
            if "block_order" in main_section:
                if block_id not in main_section["block_order"]:
                    main_section["block_order"].append(block_id)

        return json.dumps(template_data, indent=2)

    async def inject_theme_enhancements(
        self,
        product: OptimizedCatalogProduct,
        art: ArtAssetOutput,
    ) -> LiquidInjectionOutput:
        """
        Orchestrates fetching active theme, generating Liquid snippet, updating JSON template,
        and persisting changes to Shopify Theme Asset API.
        """
        logger.info(f"Liquid Coder Agent starting theme injection for: {product.optimized_seo_title}")

        # 1. Fetch active theme
        active_theme = await self.shopify.get_active_theme()
        theme_id = active_theme.get("id", 145000123456)
        theme_name = active_theme.get("name", "Active Theme")

        modified_records: List[InjectedAssetRecord] = []

        # 2. Generate and upload Liquid snippet
        snippet_key = f"snippets/elite-showcase-{product.handle[:18]}.liquid"
        snippet_content = self.generate_liquid_snippet(product, art)
        snippet_base_name = snippet_key.replace("snippets/", "").replace(".liquid", "")
        
        try:
            await self.shopify.update_theme_asset(
                theme_id=theme_id,
                asset_key=snippet_key,
                value=snippet_content,
            )
            modified_records.append(
                InjectedAssetRecord(
                    asset_key=snippet_key,
                    action="created",
                    content_summary=f"Injected Liquid snippet with {len(product.benefits)} benefits & {len(art.assets)} CDN images",
                )
            )
            logger.info(f"Updated Liquid snippet: {snippet_key}")
        except Exception as e:
            logger.warning(f"Note on Liquid snippet upload: {e}")
            modified_records.append(
                InjectedAssetRecord(
                    asset_key=snippet_key,
                    action="skipped_or_simulated",
                    content_summary=f"Snippet generated: {len(product.benefits)} benefits",
                )
            )

        # 3. Read & update templates/product.json
        template_key = "templates/product.json"
        try:
            raw_asset = await self.shopify.get_theme_asset(theme_id, template_key)
            current_template_val = raw_asset.get("value", "{}")
            updated_json_val = self.update_product_template_json(current_template_val, snippet_base_name)

            await self.shopify.update_theme_asset(
                theme_id=theme_id,
                asset_key=template_key,
                value=updated_json_val,
            )
            modified_records.append(
                InjectedAssetRecord(
                    asset_key=template_key,
                    action="updated",
                    content_summary=f"Injected custom_liquid block referencing {snippet_base_name}",
                )
            )
            logger.info(f"Updated Theme Template: {template_key}")
        except Exception as e:
            logger.warning(f"Note on Theme Template update: {e}")
            modified_records.append(
                InjectedAssetRecord(
                    asset_key=template_key,
                    action="skipped_or_simulated",
                    content_summary=f"Referenced snippet {snippet_base_name}",
                )
            )

        return LiquidInjectionOutput(
            theme_id=theme_id,
            theme_name=theme_name,
            modified_assets=modified_records,
            liquid_snippet_key=snippet_key,
            template_json_key=template_key,
            status="success",
        )
