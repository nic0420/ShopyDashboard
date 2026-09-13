"""
Aesthetic Enhancements & Conversion Rate Optimization (CRO) Deployer for Shopify Theme.
Injects high-converting hero sections, sticky mobile add-to-cart, trust & payment badges,
dynamic announcement bar, and product FAQ accordions.
"""

import asyncio
import logging
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import config
from tools.shopify_client import ShopifyClient
from agents.orchestrator import DropshippingPipelineOrchestrator
from utils.csv_parser import parse_csv

# Windows UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(force_terminal=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


HERO_BANNER_SECTION_LIQUID = """{% comment %}
  Athletic Elite Hero Banner Section
  Theme: Horizon / High-Conversion Modern E-Commerce
{% endcomment %}

<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@700;800;900&family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');

  .elite-hero-container {
    position: relative;
    background: #090D16;
    background: radial-gradient(circle at 50% 20%, #1E293B 0%, #090D16 100%);
    color: #FFFFFF;
    padding: 80px 24px 70px 24px;
    border-radius: 20px;
    margin: 20px auto 40px auto;
    max-width: 1320px;
    overflow: hidden;
    text-align: center;
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    font-family: 'Plus Jakarta Sans', sans-serif;
  }
  .elite-hero-glow {
    position: absolute;
    top: -120px;
    left: 50%;
    transform: translateX(-50%);
    width: 600px;
    height: 300px;
    background: radial-gradient(circle, rgba(16, 185, 129, 0.25) 0%, rgba(59, 130, 246, 0.15) 50%, transparent 70%);
    filter: blur(50px);
    pointer-events: none;
  }
  .elite-hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.4);
    color: #34D399;
    font-size: 0.82rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    padding: 8px 18px;
    border-radius: 9999px;
    margin-bottom: 20px;
    text-transform: uppercase;
  }
  .elite-hero-title {
    font-family: 'Outfit', sans-serif;
    font-size: clamp(2.2rem, 5vw, 3.8rem);
    font-weight: 900;
    line-height: 1.1;
    letter-spacing: -0.03em;
    margin: 0 auto 18px auto;
    max-width: 900px;
    background: linear-gradient(180deg, #FFFFFF 0%, #CBD5E1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .elite-hero-subtitle {
    font-size: clamp(1rem, 2vw, 1.25rem);
    color: #94A3B8;
    max-width: 680px;
    margin: 0 auto 32px auto;
    line-height: 1.6;
  }
  .elite-hero-cta-group {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
    margin-bottom: 40px;
  }
  .elite-btn-primary {
    background: linear-gradient(135deg, #10B981 0%, #059669 100%);
    color: #FFFFFF;
    font-weight: 800;
    font-size: 1.05rem;
    padding: 16px 36px;
    border-radius: 12px;
    text-decoration: none;
    display: inline-block;
    box-shadow: 0 10px 20px -5px rgba(16, 185, 129, 0.4);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    letter-spacing: 0.02em;
  }
  .elite-btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 14px 28px -5px rgba(16, 185, 129, 0.5);
    color: #FFFFFF;
  }
  .elite-hero-features {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    max-width: 950px;
    margin: 0 auto;
    padding-top: 30px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
  }
  .elite-feature-pill {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    font-size: 0.88rem;
    font-weight: 700;
    color: #E2E8F0;
  }
</style>

<div class="elite-hero-container">
  <div class="elite-hero-glow"></div>
  
  <div class="elite-hero-badge">
    <span>🏆</span> 2026 OFFICIAL ATHLETIC GEAR
  </div>

  <h1 class="elite-hero-title">
    DOMINA CADA LEVANTAMIENTO.<br>SUPERA TUS LÍMITES.
  </h1>

  <p class="elite-hero-subtitle">
    Equipamiento de grado profesional para atletas de alto rendimiento. Rodilleras SCR 7mm, cinturones auto-lock y cuerdas de velocidad de doble rodamiento.
  </p>

  <div class="elite-hero-cta-group">
    <a href="/collections/all" class="elite-btn-primary">
      🔥 EXPLORAR COLECCIÓN DE ÉLITE
    </a>
  </div>

  <div class="elite-hero-features">
    <div class="elite-feature-pill">
      <span>🚚</span> Envío Gratis Asegurado
    </div>
    <div class="elite-feature-pill">
      <span>🛡️</span> Neopreno & Nylon Reforzado
    </div>
    <div class="elite-feature-pill">
      <span>🔄</span> 30 Días de Garantía Total
    </div>
    <div class="elite-feature-pill">
      <span>⚡</span> Calidad Aprobada por Atletas
    </div>
  </div>
</div>
"""


TRUST_BAR_SNIPPET_LIQUID = """{% comment %}
  Global Trust & Conversion Bar for Shopify Store
{% endcomment %}

<style>
  .site-trust-bar-wrap {
    background: #0F172A;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    padding: 16px 20px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }
  .site-trust-bar-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
    max-width: 1200px;
    margin: 0 auto;
    text-align: center;
  }
  .site-trust-item {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    color: #F1F5F9;
  }
  .site-trust-icon {
    font-size: 1.4rem;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.3);
    width: 38px;
    height: 38px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
  }
  .site-trust-text h5 {
    margin: 0;
    font-size: 0.88rem;
    font-weight: 700;
    color: #FFFFFF;
    text-align: left;
  }
  .site-trust-text p {
    margin: 2px 0 0 0;
    font-size: 0.76rem;
    color: #94A3B8;
    text-align: left;
  }
</style>

<div class="site-trust-bar-wrap">
  <div class="site-trust-bar-grid">
    <div class="site-trust-item">
      <div class="site-trust-icon">🚚</div>
      <div class="site-trust-text">
        <h5>Envío Rápido Asegurado</h5>
        <p>Seguimiento online en tiempo real</p>
      </div>
    </div>
    <div class="site-trust-item">
      <div class="site-trust-icon">🛡️</div>
      <div class="site-trust-text">
        <h5>Grado Profesional Certificado</h5>
        <p>Materiales de máxima resistencia y durabilidad</p>
      </div>
    </div>
    <div class="site-trust-item">
      <div class="site-trust-icon">🔄</div>
      <div class="site-trust-text">
        <h5>30 Días de Garantía Total</h5>
        <p>Satisfacción garantizada o reembolso</p>
      </div>
    </div>
    <div class="site-trust-item">
      <div class="site-trust-icon">🔒</div>
      <div class="site-trust-text">
        <h5>Pago 100% Cifrado</h5>
        <p>Checkout seguro SSL de 256 bits</p>
      </div>
    </div>
  </div>
</div>
"""


STICKY_ADD_TO_CART_SNIPPET_LIQUID = """{% comment %}
  Sticky Mobile & Desktop Add-to-Cart Bar (High CRO)
{% endcomment %}

<style>
  .sticky-cart-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: rgba(15, 23, 42, 0.96);
    backdrop-filter: blur(12px);
    border-top: 1px solid rgba(255, 255, 255, 0.12);
    box-shadow: 0 -10px 25px rgba(0, 0, 0, 0.4);
    padding: 12px 20px;
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: space-between;
    transform: translateY(110%);
    transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
  }
  .sticky-cart-bar.is-visible {
    transform: translateY(0);
  }
  .sticky-cart-product {
    display: flex;
    align-items: center;
    gap: 14px;
    overflow: hidden;
  }
  .sticky-cart-img {
    width: 44px;
    height: 44px;
    border-radius: 8px;
    object-fit: cover;
    background: #1E293B;
  }
  .sticky-cart-info h4 {
    margin: 0;
    color: #FFFFFF;
    font-size: 0.92rem;
    font-weight: 700;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 260px;
  }
  .sticky-cart-price {
    margin: 2px 0 0 0;
    color: #34D399;
    font-weight: 800;
    font-size: 0.95rem;
  }
  .sticky-cart-actions {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .sticky-cart-btn {
    background: linear-gradient(135deg, #10B981 0%, #059669 100%);
    color: #FFFFFF;
    border: none;
    font-weight: 800;
    font-size: 0.95rem;
    padding: 12px 24px;
    border-radius: 10px;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
    transition: opacity 0.2s ease, transform 0.2s ease;
    white-space: nowrap;
  }
  .sticky-cart-btn:hover {
    opacity: 0.95;
    transform: scale(1.02);
  }
  @media (max-width: 640px) {
    .sticky-cart-bar {
      padding: 10px 14px;
    }
    .sticky-cart-info h4 {
      max-width: 140px;
      font-size: 0.82rem;
    }
    .sticky-cart-btn {
      padding: 10px 18px;
      font-size: 0.85rem;
    }
  }
</style>

<div id="stickyCartBar" class="sticky-cart-bar">
  <div class="sticky-cart-product">
    <img src="{{ product.featured_image | image_url: width: 100 }}" alt="{{ product.title }}" class="sticky-cart-img">
    <div class="sticky-cart-info">
      <h4>{{ product.title }}</h4>
      <p class="sticky-cart-price">{{ product.price | money }}</p>
    </div>
  </div>
  <div class="sticky-cart-actions">
    <button type="button" class="sticky-cart-btn" onclick="document.querySelector('form[action*=\'/cart/add\'] button[type=\'submit\']')?.click() || window.scrollTo({top: 0, behavior: 'smooth'});">
      🛒 Comprar Ahora
    </button>
  </div>
</div>

<script>
  (function() {
    var bar = document.getElementById('stickyCartBar');
    if (!bar) return;
    window.addEventListener('scroll', function() {
      if (window.scrollY > 400) {
        bar.classList.add('is-visible');
      } else {
        bar.classList.remove('is-visible');
      }
    });
  })();
</script>
"""


DYNAMIC_ANNOUNCEMENT_BAR_LIQUID = """{% comment %}
  Dynamic Announcement & Trust Bar
{% endcomment %}

<style>
  .dynamic-announcement-bar {
    background: linear-gradient(90deg, #090D16 0%, #1E293B 50%, #090D16 100%);
    color: #F8FAFC;
    padding: 8px 16px;
    font-size: 0.82rem;
    font-weight: 700;
    text-align: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 24px;
    overflow: hidden;
  }
  .dynamic-announcement-item {
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }
  .dynamic-announcement-item span.highlight {
    color: #34D399;
  }
</style>

<div class="dynamic-announcement-bar">
  <div class="dynamic-announcement-item">
    <span>🚚</span> <span>ENVÍO GRATIS Y ASEGURADO EN TODOS LOS PEDIDOS</span>
  </div>
  <div class="dynamic-announcement-item" style="opacity: 0.85;">
    <span>🔒</span> <span class="highlight">PAGO 100% SEGURO SSL</span>
  </div>
  <div class="dynamic-announcement-item" style="opacity: 0.85;">
    <span>🔄</span> <span>30 DÍAS DE GARANTÍA DE SATISFACCIÓN</span>
  </div>
</div>
"""


TRUST_PAYMENT_BADGES_LIQUID = """{% comment %}
  High Resolution Vector Payment & Security Badges
{% endcomment %}

<style>
  .payment-security-badges {
    margin: 20px 0;
    padding: 16px;
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    text-align: center;
  }
  .payment-badges-title {
    font-size: 0.8rem;
    font-weight: 700;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 10px;
  }
  .payment-badges-row {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }
  .payment-pill {
    background: #1E293B;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 0.78rem;
    font-weight: 800;
    color: #F1F5F9;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
</style>

<div class="payment-security-badges">
  <div class="payment-badges-title">PAGO 100% PROTEGIDO Y CIFRADO</div>
  <div class="payment-badges-row">
    <div class="payment-pill">💳 Visa / Mastercard</div>
    <div class="payment-pill">💳 American Express</div>
    <div class="payment-pill">🅿️ PayPal / Apple Pay</div>
    <div class="payment-pill">🔒 SSL 256-Bit</div>
  </div>
</div>
"""


PRODUCT_FAQ_ACCORDION_LIQUID = """{% comment %}
  Product FAQ Accordion for CRO
{% endcomment %}

<style>
  .product-faq-wrap {
    margin: 28px 0;
    font-family: inherit;
  }
  .product-faq-wrap h4 {
    font-size: 1.1rem;
    font-weight: 800;
    color: #111827;
    margin-bottom: 14px;
  }
  .faq-accordion-item {
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    margin-bottom: 8px;
    overflow: hidden;
  }
  .faq-accordion-item summary {
    padding: 14px 16px;
    font-weight: 700;
    font-size: 0.94rem;
    color: #1F2937;
    cursor: pointer;
    background: #F9FAFB;
    list-style: none;
    display: flex;
    justify-content: space-between;
    align-items: center;
    user-select: none;
  }
  .faq-accordion-item summary::-webkit-details-marker {
    display: none;
  }
  .faq-accordion-item summary::after {
    content: '+';
    font-size: 1.2rem;
    font-weight: bold;
    color: #6B7280;
  }
  .faq-accordion-item[open] summary::after {
    content: '−';
  }
  .faq-accordion-content {
    padding: 14px 16px;
    font-size: 0.88rem;
    color: #4B5563;
    line-height: 1.5;
    background: #FFFFFF;
    border-top: 1px solid #E5E7EB;
  }
</style>

<div class="product-faq-wrap">
  <h4>Preguntas Frecuentes</h4>
  <details class="faq-accordion-item">
    <summary>¿Cuánto tarda en llegar mi pedido?</summary>
    <div class="faq-accordion-content">
      Procesamos los pedidos en 24-48 horas. El tiempo estimado de entrega asegurada es de 5 a 12 días laborables con número de seguimiento en tiempo real.
    </div>
  </details>
  <details class="faq-accordion-item">
    <summary>¿Qué garantía tiene mi compra?</summary>
    <div class="faq-accordion-content">
      Ofrecemos 30 días de garantía de satisfacción total. Si el producto llega defectuoso o no cumple con tus expectativas, te devolvemos el 100% de tu dinero.
    </div>
  </details>
  <details class="faq-accordion-item">
    <summary>¿Cómo puedo rastrear mi paquete?</summary>
    <div class="faq-accordion-content">
      Una vez despachado tu pedido, recibirás un correo electrónico automático con el código de rastreo para consultar el estado en nuestra página de Seguimiento de Envíos.
    </div>
  </details>
</div>
"""


async def main():
    console.print(Panel(
        "[bold cyan]🎨 Desplegador de Estética, CRO & Conversión para Tienda Shopify[/bold cyan]\n"
        f"Tienda Objetivo: [bold yellow]{config.SHOP_DOMAIN}[/bold yellow]",
        title="Shopify CRO Engine",
        border_style="cyan"
    ))

    client = ShopifyClient(dry_run=config.DRY_RUN)

    # 1. Fetch Active Theme
    active_theme = await client.get_active_theme()
    theme_id = active_theme.get("id", 164813537509)
    theme_name = active_theme.get("name", "Horizon")
    console.print(f"[bold green]✔ Tema Activo Identificado:[/] {theme_name} (ID: {theme_id})\n")

    # 2. Upload Trust Bar Snippet
    console.print("[bold yellow]Paso 1:[/] Subiendo snippet de Barra de Confianza Global (`snippets/elite-trust-bar.liquid`)...")
    try:
        await client.update_theme_asset(
            theme_id=theme_id,
            asset_key="snippets/elite-trust-bar.liquid",
            value=TRUST_BAR_SNIPPET_LIQUID.strip()
        )
        console.print("[bold green]✔ Snippet `snippets/elite-trust-bar.liquid` subido con éxito.[/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Error al subir trust bar snippet: {e}[/bold red]")

    # 3. Upload Sticky Cart Snippet
    console.print("\n[bold yellow]Paso 2:[/] Subiendo Sticky Add-to-Cart Móvil (`snippets/elite-sticky-cart.liquid`)...")
    try:
        await client.update_theme_asset(
            theme_id=theme_id,
            asset_key="snippets/elite-sticky-cart.liquid",
            value=STICKY_ADD_TO_CART_SNIPPET_LIQUID.strip()
        )
        console.print("[bold green]✔ Snippet `snippets/elite-sticky-cart.liquid` subido con éxito.[/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Error al subir sticky cart snippet: {e}[/bold red]")

    # 4. Upload Dynamic Announcement Bar Snippet
    console.print("\n[bold yellow]Paso 3:[/] Subiendo Barra de Anuncios Dinámica (`snippets/elite-announcement-bar.liquid`)...")
    try:
        await client.update_theme_asset(
            theme_id=theme_id,
            asset_key="snippets/elite-announcement-bar.liquid",
            value=DYNAMIC_ANNOUNCEMENT_BAR_LIQUID.strip()
        )
        console.print("[bold green]✔ Snippet `snippets/elite-announcement-bar.liquid` subido con éxito.[/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Error al subir announcement bar: {e}[/bold red]")

    # 5. Upload Payment Badges Snippet
    console.print("\n[bold yellow]Paso 4:[/] Subiendo Badges de Pago Seguro (`snippets/elite-payment-badges.liquid`)...")
    try:
        await client.update_theme_asset(
            theme_id=theme_id,
            asset_key="snippets/elite-payment-badges.liquid",
            value=TRUST_PAYMENT_BADGES_LIQUID.strip()
        )
        console.print("[bold green]✔ Snippet `snippets/elite-payment-badges.liquid` subido con éxito.[/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Error al subir payment badges: {e}[/bold red]")

    # 6. Upload FAQ Accordion Snippet
    console.print("\n[bold yellow]Paso 5:[/] Subiendo Acordeón de FAQ (`snippets/elite-faq-accordion.liquid`)...")
    try:
        await client.update_theme_asset(
            theme_id=theme_id,
            asset_key="snippets/elite-faq-accordion.liquid",
            value=PRODUCT_FAQ_ACCORDION_LIQUID.strip()
        )
        console.print("[bold green]✔ Snippet `snippets/elite-faq-accordion.liquid` subido con éxito.[/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Error al subir FAQ accordion: {e}[/bold red]")

    # 7. Upload Hero Section
    console.print("\n[bold yellow]Paso 6:[/] Subiendo Sección Hero Premium (`sections/elite-hero-banner.liquid`)...")
    try:
        await client.update_theme_asset(
            theme_id=theme_id,
            asset_key="sections/elite-hero-banner.liquid",
            value=HERO_BANNER_SECTION_LIQUID.strip()
        )
        console.print("[bold green]✔ Sección `sections/elite-hero-banner.liquid` subida con éxito.[/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Error al subir hero section: {e}[/bold red]")

    # 8. Re-execute Multi-Agent Pipeline to update all product snippets
    console.print("\n[bold yellow]Paso 7:[/] Actualizando fichas y snippets Liquid de los productos del catálogo...")
    orchestrator = DropshippingPipelineOrchestrator(shopify_client=client)
    items = parse_csv("data/catalogo_proveedor.csv")

    for idx, item in enumerate(items, start=1):
        title = item.get("raw_title", "Producto")
        console.print(f"  ▶ Procesando producto [{idx}/{len(items)}]: {title[:45]}...")
        await orchestrator.run(item)

    console.print(Panel(
        "[bold green]✨ ¡Fase 2 de Transformación Visual & CRO Desplegada con Éxito![/bold green]\n\n"
        "1. [bold]Hero Banner Premium:[/bold] `sections/elite-hero-banner.liquid`\n"
        "2. [bold]Barra de Confianza Global:[/bold] `snippets/elite-trust-bar.liquid`\n"
        "3. [bold]Sticky Add-to-Cart Móvil:[/bold] `snippets/elite-sticky-cart.liquid`\n"
        "4. [bold]Barra Dinámica Superior:[/bold] `snippets/elite-announcement-bar.liquid`\n"
        "5. [bold]Badges de Pago Seguro:[/bold] `snippets/elite-payment-badges.liquid`\n"
        "6. [bold]Acordeón de Preguntas Frecuentes (FAQ):[/bold] `snippets/elite-faq-accordion.liquid`",
        title="Estado de Despliegue",
        border_style="green"
    ))


if __name__ == "__main__":
    asyncio.run(main())
