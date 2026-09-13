"""
Full Store Automation: Configures Navigation Menus (Footer & Main) and Injects CRO Suite into Active Theme.
"""

import asyncio
import json
import logging
import re
import sys
from rich.console import Console
from rich.panel import Panel

from config import config
from tools.shopify_client import ShopifyClient

# Windows UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(force_terminal=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


FOOTER_MENU_ITEMS = [
    {"title": "Buscar", "url": "/search", "type": "HTTP"},
    {"title": "Política de Envíos", "url": "/pages/politica-de-envios", "type": "HTTP"},
    {"title": "Garantía y Reembolsos", "url": "/pages/politica-de-reembolso", "type": "HTTP"},
    {"title": "Preguntas Frecuentes (FAQ)", "url": "/pages/preguntas-frecuentes", "type": "HTTP"},
    {"title": "Rastreo de Pedido", "url": "/pages/rastreo-de-pedido", "type": "HTTP"},
    {"title": "Términos del Servicio", "url": "/pages/terminos-del-servicio", "type": "HTTP"},
]

MAIN_MENU_ITEMS = [
    {"title": "Inicio", "url": "/", "type": "HTTP"},
    {"title": "Catálogo", "url": "/collections/all", "type": "HTTP"},
    {"title": "Rastrear Pedido", "url": "/pages/rastreo-de-pedido", "type": "HTTP"},
    {"title": "Preguntas Frecuentes", "url": "/pages/preguntas-frecuentes", "type": "HTTP"},
]


async def update_navigation_menus(client: ShopifyClient):
    console.print("\n[bold yellow]Paso 1:[/] Configurando menús de navegación en Shopify...")

    query_menus = """
    query {
      menus(first: 10) {
        nodes {
          id
          title
          handle
        }
      }
    }
    """
    res = await client.graphql(query_menus)
    menus = res.get("data", {}).get("menus", {}).get("nodes", [])

    footer_menu_id = None
    main_menu_id = None

    for m in menus:
        if m.get("handle") == "footer":
            footer_menu_id = m.get("id")
        elif m.get("handle") == "main-menu":
            main_menu_id = m.get("id")

    mutation_update = """
    mutation menuUpdate($id: ID!, $title: String!, $handle: String!, $items: [MenuItemUpdateInput!]!) {
      menuUpdate(id: $id, title: $title, handle: $handle, items: $items) {
        menu {
          id
          title
        }
        userErrors {
          field
          message
        }
      }
    }
    """

    # 1. Update Footer Menu
    if footer_menu_id:
        vars_footer = {
            "id": footer_menu_id,
            "title": "Pie de Página",
            "handle": "footer",
            "items": [{"title": it["title"], "url": it["url"], "type": it["type"]} for it in FOOTER_MENU_ITEMS]
        }
        f_res = await client.graphql(mutation_update, vars_footer)
        errs = f_res.get("data", {}).get("menuUpdate", {}).get("userErrors", [])
        if not errs:
            console.print("  [bold green]✔ Menú de Pie de Página (Footer) actualizado con las 5 páginas legales y buscador.[/bold green]")
        else:
            console.print(f"  [bold red]❌ Error en Footer Menu: {errs}[/bold red]")

    # 2. Update Main Menu
    if main_menu_id:
        vars_main = {
            "id": main_menu_id,
            "title": "Menú Principal",
            "handle": "main-menu",
            "items": [{"title": it["title"], "url": it["url"], "type": it["type"]} for it in MAIN_MENU_ITEMS]
        }
        m_res = await client.graphql(mutation_update, vars_main)
        errs = m_res.get("data", {}).get("menuUpdate", {}).get("userErrors", [])
        if not errs:
            console.print("  [bold green]✔ Menú Principal actualizado con Catálogo, Rastreo y FAQ.[/bold green]")
        else:
            console.print(f"  [bold red]❌ Error en Main Menu: {errs}[/bold red]")


async def inject_theme_widgets(client: ShopifyClient):
    console.print("\n[bold yellow]Paso 2:[/] Inyectando widgets de conversión en el tema activo...")

    active_theme = await client.get_active_theme()
    theme_id = active_theme.get("id", 164813537509)

    # 1. Update layout/theme.liquid
    theme_asset = await client.get_theme_asset(theme_id, "layout/theme.liquid")
    theme_val = theme_asset.get("value", "")

    if "elite-social-proof" not in theme_val:
        injection_code = """
  {% comment %} Injected Elite CRO Widgets {% endcomment %}
  {% render 'elite-social-proof' %}
  {% render 'elite-drawer-cart' %}
</body>
"""
        theme_val = theme_val.replace("</body>", injection_code)
        await client.update_theme_asset(theme_id, "layout/theme.liquid", theme_val)
        console.print("  [bold green]✔ Social Proof & Drawer Cart inyectados globalmente en `layout/theme.liquid`.[/bold green]")
    else:
        console.print("  [bold cyan]ℹ `layout/theme.liquid` ya contiene los widgets CRO.[/bold cyan]")


PRODUCT_CRO_INJECTION_LIQUID = """{% comment %}
  Elite CRO Injected Product Conversion Block
{% endcomment %}
{% render 'elite-stock-countdown' %}
{% render 'elite-volume-discounts' %}
{% render 'elite-payment-badges' %}
{% render 'elite-sticky-cart' %}
{% render 'elite-faq-accordion' %}
"""

ELITE_CRO_SECTION_LIQUID = """{% comment %}
  Elite CRO Section for Product Page
{% endcomment %}
<div class="elite-cro-section-wrapper" style="max-width: 1200px; margin: 20px auto; padding: 0 20px;">
  {% render 'elite-product-cro-suite' %}
</div>

{% schema %}
{
  "name": "Elite CRO Suite",
  "settings": [],
  "presets": [
    {
      "name": "Elite CRO Suite"
    }
  ]
}
{% endschema %}
"""


async def inject_product_template_widgets(client: ShopifyClient):
    console.print("\n[bold yellow]Paso 3:[/] Inyectando bloques de oferta en la ficha de producto...")

    active_theme = await client.get_active_theme()
    theme_id = active_theme.get("id", 164813537509)

    # 1. Upload unified product CRO snippet
    snippet_key = "snippets/elite-product-cro-suite.liquid"
    await client.update_theme_asset(theme_id, snippet_key, PRODUCT_CRO_INJECTION_LIQUID.strip())
    console.print(f"  [bold green]✔ Snippet `{snippet_key}` creado.[/bold green]")

    # 2. Upload section
    section_key = "sections/elite-cro-section.liquid"
    await client.update_theme_asset(theme_id, section_key, ELITE_CRO_SECTION_LIQUID.strip())
    console.print(f"  [bold green]✔ Sección `{section_key}` creada.[/bold green]")

    # 3. Update templates/product.json with custom section
    template_asset = await client.get_theme_asset(theme_id, "templates/product.json")
    template_val = template_asset.get("value", "{}")
    try:
        data = json.loads(template_val)
        data.setdefault("sections", {})
        data["sections"]["elite_cro_section"] = {
            "type": "elite-cro-section",
            "settings": {}
        }
        if "order" in data and "elite_cro_section" not in data["order"]:
            data["order"].insert(1, "elite_cro_section")
        
        updated_json = json.dumps(data, indent=2)
        await client.update_theme_asset(theme_id, "templates/product.json", updated_json)
        console.print("  [bold green]✔ Sección de conversión registrada e inyectada en `templates/product.json`.[/bold green]")
    except Exception as e:
        console.print(f"  [bold red]❌ Error al actualizar product.json: {e}[/bold red]")


async def main():
    console.print(Panel(
        "[bold cyan]🚀 Automatización Total de Tienda Shopify[/bold cyan]\n"
        f"Tienda: [bold yellow]{config.SHOP_DOMAIN}[/bold yellow]",
        title="Shopify Auto-Pilot",
        border_style="cyan"
    ))

    client = ShopifyClient(dry_run=config.DRY_RUN)

    await update_navigation_menus(client)
    await inject_theme_widgets(client)
    await inject_product_template_widgets(client)

    console.print(Panel(
        "[bold green]✨ ¡Automatización de Tienda Completada Exitosamente![/bold green]\n\n"
        "1. [bold]Menú de Pie de Página:[/bold] Conectado con Envíos, Reembolsos, FAQ, Rastreo y Términos.\n"
        "2. [bold]Menú Principal:[/bold] Conectado con Catálogo, Rastreo y FAQ.\n"
        "3. [bold]Widgets Globales:[/bold] Social Proof emergente y Carrito Deslizable activos en todo el sitio.\n"
        "4. [bold]Fichas de Producto:[/bold] Ofertas por volumen, contador de urgencia, sticky cart y badges inyectados.",
        title="Todo Listo",
        border_style="green"
    ))


if __name__ == "__main__":
    asyncio.run(main())
