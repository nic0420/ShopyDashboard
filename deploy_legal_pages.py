"""
Legal & Support Pages Deployer for Shopify Store.
Publishes Shipping Policy, Refund Guarantee, FAQ, Order Tracking, and Terms of Service.
"""

import asyncio
import logging
import sys
from pathlib import Path
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


PAGES_TO_DEPLOY = [
    {
        "title": "Política de Envíos y Entregas",
        "handle": "politica-de-envios",
        "file": "data/legal_pages/politica_de_envios.html",
    },
    {
        "title": "Garantía y Política de Reembolso",
        "handle": "politica-de-reembolso",
        "file": "data/legal_pages/politica_de_reembolso_y_garantia.html",
    },
    {
        "title": "Preguntas Frecuentes (FAQ)",
        "handle": "preguntas-frecuentes",
        "file": "data/legal_pages/preguntas_frecuentes_faq.html",
    },
    {
        "title": "Seguimiento de Pedido",
        "handle": "rastreo-de-pedido",
        "file": "data/legal_pages/seguimiento_de_pedidos.html",
    },
    {
        "title": "Términos del Servicio",
        "handle": "terminos-del-servicio",
        "file": "data/legal_pages/terminos_del_servicio.html",
    },
]


async def main():
    console.print(Panel(
        "[bold cyan]📜 Desplegador Automático de Páginas Legales & Soporte para Shopify[/bold cyan]\n"
        f"Tienda Objetivo: [bold yellow]{config.SHOP_DOMAIN}[/bold yellow]",
        title="Shopify Legal Engine",
        border_style="cyan"
    ))

    client = ShopifyClient(dry_run=config.DRY_RUN)

    for idx, item in enumerate(PAGES_TO_DEPLOY, start=1):
        title = item["title"]
        handle = item["handle"]
        file_path = Path(item["file"])

        if not file_path.exists():
            console.print(f"[bold red]❌ Archivo no encontrado:[/] {file_path}")
            continue

        body_html = file_path.read_text(encoding="utf-8")
        console.print(f"[{idx}/{len(PAGES_TO_DEPLOY)}] Publicando página: [bold white]{title}[/] (`/pages/{handle}`)...")

        res = await client.create_or_update_page(
            title=title,
            body_html=body_html,
            handle=handle,
        )

        page_id = res.get("id", "OK")
        console.print(f"  [bold green]✔ Página publicada con éxito:[/] ID {page_id} -> `/pages/{handle}`")

    console.print(Panel(
        "[bold green]✨ ¡Todas las páginas legales y de atención al cliente han sido publicadas![/bold green]\n\n"
        "1. [bold]Envíos:[/bold] `/pages/politica-de-envios`\n"
        "2. [bold]Garantía & Reembolso:[/bold] `/pages/politica-de-reembolso`\n"
        "3. [bold]FAQ:[/bold] `/pages/preguntas-frecuentes`\n"
        "4. [bold]Rastreo en Vivo:[/bold] `/pages/rastreo-de-pedido`\n"
        "5. [bold]Términos:[/bold] `/pages/terminos-del-servicio`",
        title="Despliegue Completado",
        border_style="green"
    ))


if __name__ == "__main__":
    asyncio.run(main())
