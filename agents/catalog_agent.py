"""
Catalog Agent: Responsible for raw JSON/CSV ingestion, LLM-powered SEO copywriting,
benefit crafting for functional fitness athletes, structured pricing markup, and
Shopify product registration.
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import httpx
from pydantic import BaseModel, Field

from config import config
from tools.shopify_client import ShopifyClient

logger = logging.getLogger("CatalogAgent")


class BenefitItem(BaseModel):
    title: str = Field(..., description="Short punchy benefit headline")
    description: str = Field(..., description="Value proposition explanation")
    icon: str = Field(default="✨", description="Icon or emoji representation")


class OptimizedCatalogProduct(BaseModel):
    original_title: str
    optimized_seo_title: str
    handle: str
    hook: str
    benefits: List[BenefitItem]
    specs: Dict[str, str]
    description_html: str
    suggested_price: float
    compare_at_price: float
    vendor: str
    product_type: str
    tags: List[str]
    seo_keywords: List[str]
    shopify_product_id: Optional[str] = None
    generated_by_llm: bool = False


class CatalogAgent:
    """
    Agent responsible for transforming raw dropshipping supplier payloads
    into high-converting, SEO-optimized Shopify product catalog entries
    using LLM AI Copywriting with resilient deterministic fallbacks.
    """

    def __init__(
        self,
        shopify_client: ShopifyClient,
        llm_api_key: Optional[str] = None,
        llm_model: Optional[str] = None,
        llm_provider: Optional[str] = None,
    ):
        self.shopify = shopify_client
        self.llm_api_key = llm_api_key if llm_api_key is not None else config.LLM_API_KEY
        self.llm_model = llm_model or config.LLM_MODEL or "gemini-1.5-flash"
        self.llm_provider = (llm_provider or config.LLM_PROVIDER or "gemini").lower()

    # SPAM / Junk keywords commonly found in dropshipping supplier titles
    SPAM_PATTERNS = [
        r"\b(hot\s*sale|hot|dropshipping|drop\s*shipping|drop\s*ship(?:per|ping)?|dropship|wholesale|cheap|new\s*arrival|free\s*shipping|free\s*ship|top\s*quality|high\s*quality|best\s*quality|202[0-9]|factory\s*price|best\s*seller|direct\s*sale|aliexpress|cj\s*dropshipping|amazon\s*hot)\b",
        r"\b(good\s*quality|no\s*slip|anti\s*slip|fast\s*ship|men\s*women|unisex|brand\s*new|100%\s*original)\b",
        r"[\!\|\*\#\$\@\^\&\(\)]+",
    ]

    def _log_error_to_file(self, raw_title: str, error_type: str, details: str, status_code: Optional[int] = None):
        """
        Appends structured error details to error_log.txt for resilience and monitoring.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        code_str = f" [HTTP_CODE: {status_code}]" if status_code else ""
        error_line = f"[{timestamp}] [RAW_TITLE: {raw_title[:40]}]{code_str} [{error_type}] Details: {details}\n"
        logger.error(error_line.strip())
        try:
            with open("error_log.txt", "a", encoding="utf-8") as err_f:
                err_f.write(error_line)
        except Exception as file_err:
            logger.warning(f"Could not append to error_log.txt: {file_err}")

    def sanitize_customer_facing_text(self, text: str) -> str:
        """
        Sanitizes titles, handles, and copy to guarantee no supplier/dropshipping jargon leaks to the customer.
        """
        cleaned = text
        for pattern in self.SPAM_PATTERNS:
            cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def optimize_seo_title(self, raw_title: str, product_type: str = "") -> str:
        """
        Deterministic Rule-based Fallback: Synthesizes a clean, premium,
        commercial, SEO-rich title under 60 characters without trailing stop-words.
        """
        cleaned = self.sanitize_customer_facing_text(raw_title)

        # Extract core keywords
        words = [w.capitalize() for w in cleaned.split() if len(w) > 1 and w.lower() not in ("the", "and", "with", "for", "drop", "shipping", "hot", "sale")]
        
        # Build a coherent athletic/commercial title
        if any(w in words for w in ["Belt", "Cinturon", "Cinturón"]):
            final_title = "Cinturón de Nylon para Halterofilia Pro Auto-Lock"
        elif any(w in words for w in ["Knee", "Rodillera", "Rodilleras"]):
            final_title = "Rodilleras de Compresión 7mm Neopreno SCR Pro"
        elif any(w in words for w in ["Rope", "Cuerda", "Salto"]):
            final_title = "Cuerda de Salto Pro Speed con Doble Rodamiento"
        elif any(w in words for w in ["Facial", "Cleanser", "Brush", "Face"]):
            final_title = "Cepillo Limpiador Facial Sónico Pro Radiance IPX7"
        elif words:
            final_title = f"{' '.join(words[:4])} Pro Elite"
        else:
            final_title = f"Artículo Premium de {product_type.capitalize() or 'Alto Rendimiento'}"

        if len(final_title) > 60:
            final_title = final_title[:57] + "..."

        return final_title

    def generate_benefits(self, raw_payload: Dict[str, Any]) -> List[BenefitItem]:
        """
        Deterministic Rule-based Fallback: Extracts key features and turns them into benefits.
        """
        features = raw_payload.get("raw_description", raw_payload.get("features", []))
        if isinstance(features, str):
            features = [f.strip() for f in features.split("|") if f.strip()]

        default_benefits = [
            BenefitItem(
                title="Ergonomic & High-Performance Design",
                description="Engineered for daily comfort and stability during intense functional training.",
                icon="⚡",
            ),
            BenefitItem(
                title="High-Grade Reinforced Materials",
                description="Built with resilient, high-density materials ensuring durability under heavy loads.",
                icon="🛡️",
            ),
            BenefitItem(
                title="Instant Competition-Ready Setup",
                description="Optimized anatomical fit ready for competition with zero break-in period required.",
                icon="🔥",
            ),
        ]

        if features and isinstance(features, list) and len(features) > 0:
            custom_benefits = []
            icons = ["⚡", "🛡️", "🔥", "💪", "🚀"]
            for i, feat in enumerate(features[:3]):
                icon = icons[i % len(icons)]
                if isinstance(feat, dict):
                    custom_benefits.append(
                        BenefitItem(
                            title=feat.get("title", f"Beneficio Técnico {i+1}")[:40],
                            description=feat.get("description", str(feat)),
                            icon=icon,
                        )
                    )
                elif isinstance(feat, str):
                    custom_benefits.append(
                        BenefitItem(
                            title=feat[:35] + ("..." if len(feat) > 35 else ""),
                            description=feat,
                            icon=icon,
                        )
                    )
            if len(custom_benefits) == 3:
                return custom_benefits

        return default_benefits

    async def call_llm_for_copywriting(
        self,
        raw_title: str,
        raw_description: Union[str, List[str]],
        product_type: str,
        vendor: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Calls Gemini / OpenAI API with specialized Prompt Engineering for Functional Fitness Athletes.
        Enforces structured JSON output with title (<= 60 chars), persuasive copy, and 3 technical bullets.
        """
        if not self.llm_api_key:
            logger.info("LLM_API_KEY not configured. Using deterministic rule-based copywriting fallback.")
            return None

        # Format description bullets
        desc_text = "\n".join([f"- {d}" for d in raw_description]) if isinstance(raw_description, list) else str(raw_description)

        prompt = f"""
Eres un redactor publicitario de comercio electrónico de élite y especialista en SEO para marcas de fitness y entrenamiento funcional (CrossFit, powerlifting, halterofilia y calistenia).

Tu objetivo es transformar los siguientes datos crudos de un proveedor de dropshipping en un producto premium de alta conversión.

DATOS CRUDOS DEL PRODUCTO:
- Título Crudo: {raw_title}
- Categoría / Tipo: {product_type}
- Marca / Vendor: {vendor}
- Características / Descripción Cruda:
{desc_text}

REGLAS ESTRICTAS DE REDACCIÓN:
1. 'seo_title': Tienes PROHIBIDO recortar literalmente el título original. Debes analizar de qué trata el producto y redactar un título SEO completamente nuevo (máximo 60 caracteres) que suene premium, técnico y enfocado en atletas de alto rendimiento. Ejemplo esperado: 'Cinturón de Nylon para Halterofilia con Bloqueo'.
2. 'persuasive_description': Un párrafo persuasivo y emocionante (entre 45 y 75 palabras) enfocado en atletas de entrenamiento funcional, destacando soporte articular, durabilidad bajo cargas extremas y superación de marcas personales (PRs).
3. 'benefits': Un array con EXACTAMENTE 3 viñetas técnicas. Cada viñeta debe incluir:
   - 'title': Titular corto y potente (máximo 40 caracteres).
   - 'description': Explicación clara del beneficio y la ventaja competitiva.
   - 'icon': Un emoji representativo (ej. ⚡, 🛡️, 🔥, 🏆, 💎).
4. 'specs': Un diccionario con 3 o 4 especificaciones técnicas clave (ej. Material, Uso Recomendado, Ajuste, Resistencia).

Debes responder ÚNICAMENTE con un JSON válido que siga exactamente este esquema, sin comentarios ni texto adicional:
{{
  "seo_title": "string (máximo 60 caracteres)",
  "persuasive_description": "string",
  "benefits": [
    {{"title": "string", "description": "string", "icon": "string"}},
    {{"title": "string", "description": "string", "icon": "string"}},
    {{"title": "string", "description": "string", "icon": "string"}}
  ],
  "specs": {{
    "Material": "string",
    "Uso Recomendado": "string",
    "Garantía": "string"
  }}
}}
"""

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                if self.llm_provider == "openai":
                    url = "https://api.openai.com/v1/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {self.llm_api_key}",
                        "Content-Type": "application/json",
                    }
                    body = {
                        "model": self.llm_model,
                        "messages": [
                            {"role": "system", "content": "You are a high-converting e-commerce copywriter. Return only valid JSON."},
                            {"role": "user", "content": prompt},
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.3,
                    }
                    resp = await client.post(url, headers=headers, json=body)
                    resp.raise_for_status()
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                else:
                    # Default: Google Gemini API
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.llm_model}:generateContent?key={self.llm_api_key}"
                    headers = {"Content-Type": "application/json"}
                    body = {
                        "contents": [
                            {
                                "parts": [{"text": prompt}]
                            }
                        ],
                        "generationConfig": {
                            "response_mime_type": "application/json",
                            "temperature": 0.3,
                        },
                    }
                    resp = await client.post(url, headers=headers, json=body)
                    if resp.status_code == 429:
                        self._log_error_to_file(raw_title, "LLM_QUOTA_EXCEEDED", "Gemini API rate limit or quota exceeded (HTTP 429)", 429)
                        return None
                    elif resp.status_code == 401:
                        self._log_error_to_file(raw_title, "LLM_UNAUTHORIZED", "Invalid LLM_API_KEY provided (HTTP 401)", 401)
                        return None
                    
                    resp.raise_for_status()
                    data = resp.json()
                    content = data["candidates"][0]["content"]["parts"][0]["text"]

                # Clean JSON markdown if wrapped in ```json
                clean_json_str = content.strip()
                if clean_json_str.startswith("```"):
                    clean_json_str = re.sub(r"^```(?:json)?\n?", "", clean_json_str)
                    clean_json_str = re.sub(r"\n?```$", "", clean_json_str)

                parsed_json = json.loads(clean_json_str.strip())
                logger.info(f"✔ LLM successfully generated copy for: '{parsed_json.get('seo_title')}'")
                return parsed_json

        except httpx.HTTPStatusError as http_err:
            self._log_error_to_file(raw_title, "LLM_HTTP_ERROR", f"{http_err.response.status_code}: {http_err.response.text}", http_err.response.status_code)
            return None
        except httpx.RequestError as req_err:
            self._log_error_to_file(raw_title, "LLM_NETWORK_TIMEOUT", str(req_err))
            return None
        except Exception as e:
            self._log_error_to_file(raw_title, "LLM_PARSING_ERROR", str(e))
            return None

    def build_description_html(
        self,
        seo_title: str,
        hook: str,
        benefits: List[BenefitItem],
        specs: Dict[str, str],
    ) -> str:
        """
        Assembles a conversion-rate optimized HTML description block.
        """
        benefits_html = "".join(
            f"""
            <div class="product-benefit-item" style="margin-bottom: 12px; display: flex; align-items: flex-start; gap: 10px;">
                <span style="font-size: 1.25rem;">{b.icon}</span>
                <div>
                    <strong style="color: #111827; font-size: 1rem;">{b.title}</strong>
                    <p style="margin: 2px 0 0 0; color: #4B5563; font-size: 0.92rem; line-height: 1.4;">{b.description}</p>
                </div>
            </div>
            """
            for b in benefits
        )

        specs_html = "".join(
            f"""
            <tr style="border-bottom: 1px solid #E5E7EB;">
                <td style="padding: 8px 12px; font-weight: 600; color: #374151; background: #F9FAFB; width: 40%;">{k}</td>
                <td style="padding: 8px 12px; color: #6B7280;">{v}</td>
            </tr>
            """
            for k, v in specs.items()
        )

        html = f"""
        <div class="shopify-optimized-product-description" style="font-family: inherit; line-height: 1.6; color: #1F2937;">
            <div class="hero-hook" style="background: linear-gradient(135deg, #F3F4F6 0%, #E5E7EB 100%); padding: 18px 20px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="margin: 0 0 8px 0; color: #111827; font-size: 1.15rem; font-weight: 700;">{seo_title}</h3>
                <p style="margin: 0; font-size: 0.98rem; color: #374151;">{hook}</p>
            </div>

            <h4 style="font-size: 1.05rem; font-weight: 700; color: #111827; margin: 24px 0 14px 0; border-bottom: 2px solid #3B82F6; padding-bottom: 6px; display: inline-block;">
                ¿Por Qué Te Encantará?
            </h4>
            <div class="benefits-container" style="margin-bottom: 24px;">
                {benefits_html}
            </div>

            <h4 style="font-size: 1.05rem; font-weight: 700; color: #111827; margin: 24px 0 14px 0; border-bottom: 2px solid #3B82F6; padding-bottom: 6px; display: inline-block;">
                Especificaciones Técnicas
            </h4>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; border: 1px solid #E5E7EB; border-radius: 6px; overflow: hidden; font-size: 0.9rem;">
                <tbody>
                    {specs_html}
                </tbody>
            </table>

            <div class="trust-badges" style="display: flex; justify-content: space-around; background: #ECFDF5; border: 1px solid #A7F3D0; padding: 14px; border-radius: 8px; text-align: center; margin-top: 20px;">
                <div><span style="font-size: 1.2rem;">🚚</span><br><small style="color: #065F46; font-weight: 600;">Envío Rápido Asegurado</small></div>
                <div><span style="font-size: 1.2rem;">🔒</span><br><small style="color: #065F46; font-weight: 600;">Pago 100% Seguro</small></div>
                <div><span style="font-size: 1.2rem;">🔄</span><br><small style="color: #065F46; font-weight: 600;">30 Días de Garantía</small></div>
            </div>
        </div>
        """
        return html.strip()

    async def process_payload(self, raw_payload: Dict[str, Any]) -> OptimizedCatalogProduct:
        """
        Ingests the raw dropshipping payload, invokes the LLM for high-converting copy
        (with automatic deterministic fallback on failure), formats HTML, and registers in Shopify.
        """
        raw_title = raw_payload.get("raw_title", raw_payload.get("title", "Dropshipping Item"))
        raw_description = raw_payload.get("raw_description", raw_payload.get("description", raw_payload.get("features", [])))
        product_type = raw_payload.get("product_type", raw_payload.get("category", "Fitness Equipment"))
        vendor = raw_payload.get("vendor", "ApexGrip Athletics")

        logger.info(f"Processing catalog payload for: '{raw_title[:50]}...'")

        # 1. Attempt LLM Copywriting Generation
        llm_data = await self.call_llm_for_copywriting(
            raw_title=raw_title,
            raw_description=raw_description,
            product_type=product_type,
            vendor=vendor,
        )

        generated_by_llm = False

        if llm_data and isinstance(llm_data, dict):
            # Use LLM Copy with strict sanitization
            raw_seo_title = str(llm_data.get("seo_title", "")).strip()
            seo_title = self.sanitize_customer_facing_text(raw_seo_title)
            if len(seo_title) > 60:
                seo_title = seo_title[:57] + "..."
            if not seo_title:
                seo_title = self.optimize_seo_title(raw_title, product_type)

            hook = str(llm_data.get("persuasive_description", "")).strip()
            
            raw_benefits = llm_data.get("benefits", [])
            benefits = []
            for b in raw_benefits[:3]:
                if isinstance(b, dict):
                    benefits.append(
                        BenefitItem(
                            title=str(b.get("title", "Beneficio Clave")),
                            description=str(b.get("description", "")),
                            icon=str(b.get("icon", "⚡")),
                        )
                    )
            if len(benefits) < 3:
                benefits = self.generate_benefits(raw_payload)

            specs = llm_data.get("specs", {})
            if not isinstance(specs, dict) or not specs:
                specs = {
                    "Material": "SCR Neoprene / Aleación Reforzada",
                    "Uso Recomendado": "Entrenamiento Funcional, Levantamiento, WODs",
                    "Garantía": "12 meses oficial",
                }

            generated_by_llm = True
            logger.info(f"✔ Using LLM-generated copy for product: '{seo_title}'")

        else:
            # Deterministic Fallback Mode
            logger.info(f"Executing deterministic fallback copywriting for: '{raw_title[:40]}'")
            seo_title = self.optimize_seo_title(raw_title, product_type)
            hook = raw_payload.get(
                "hook",
                f"Diseñado para deportistas y atletas exigentes: máxima estabilidad, durabilidad y rendimiento garantizado.",
            )
            benefits = self.generate_benefits(raw_payload)
            specs = raw_payload.get("specs", {})
            if not specs:
                specs = {
                    "Material": "SCR Neoprene de Grado Médico & Polímero Reforzado",
                    "Ajuste": "Contorno Anatómico 3D Antideslizante",
                    "Uso Recomendado": "CrossFit, Halterofilia, Powerlifting",
                    "Garantía": "12 Meses Oficial",
                }

        # 2. Handle & SEO Keywords (Sanitized)
        handle = seo_title.lower().replace(" ", "-").replace("/", "-")
        handle = re.sub(r"[^a-z0-9\-]", "", handle)
        handle = re.sub(r"-+", "-", handle).strip("-")

        # 3. Pricing & Markup (Dropshipping Margin 2.5x standard)
        supplier_cost = float(raw_payload.get("base_cost", raw_payload.get("cost", raw_payload.get("price", 19.99))))
        suggested_price = round(supplier_cost * 2.5, 2)
        compare_at_price = round(suggested_price * 1.45, 2)

        # 4. HTML Description Assembly
        description_html = self.build_description_html(seo_title, hook, benefits, specs)

        # 5. Clean Customer-Facing Tags & Keywords (Never expose dropshipping jargon)
        forbidden_tags = {"dropshipping", "drop", "shipping", "hot", "sale", "wholesale", "cheap", "cj"}
        base_keywords = [
            w.lower()
            for w in re.split(r"[\s\-]+", seo_title)
            if len(w) > 3 and w.lower() not in forbidden_tags
        ]
        tags = list(set(["premium", "trending", "calidad-garantizada", product_type.lower()] + base_keywords))

        # Reference images from supplier CSV
        ref_imgs = raw_payload.get("reference_images", [])
        if isinstance(ref_imgs, str):
            ref_imgs = [u.strip() for u in ref_imgs.split(",") if u.strip()]

        # 6. Create in Shopify via ShopifyClient
        shopify_input = {
            "title": seo_title,
            "descriptionHtml": description_html,
            "vendor": vendor,
            "productType": product_type,
            "tags": tags,
            "status": "ACTIVE",
            "images": ref_imgs,
            "variants": [
                {
                    "price": str(suggested_price),
                    "compareAtPrice": str(compare_at_price),
                    "sku": f"DS-{handle[:8].upper()}-01",
                    "inventoryQuantity": 150,
                }
            ],
        }


        shopify_resp = await self.shopify.create_product(shopify_input)
        created_prod = shopify_resp.get("data", {}).get("productCreate", {}).get("product", {})
        shopify_product_id = created_prod.get("id")

        logger.info(f"Successfully processed catalog product. Shopify Product ID: {shopify_product_id}")

        return OptimizedCatalogProduct(
            original_title=raw_title,
            optimized_seo_title=seo_title,
            handle=handle,
            hook=hook,
            benefits=benefits,
            specs=specs,
            description_html=description_html,
            suggested_price=suggested_price,
            compare_at_price=compare_at_price,
            vendor=vendor,
            product_type=product_type,
            tags=tags,
            seo_keywords=base_keywords,
            shopify_product_id=shopify_product_id,
            generated_by_llm=generated_by_llm,
        )
