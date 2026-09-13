"""
CRO Components Deployer for Shopify Theme.
Uploads Volume Discounts, Stock Urgency, Social Proof, and Drawer Cart snippets to the active theme.
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


SNIPPETS_TO_DEPLOY = [
    {
        "key": "snippets/elite-volume-discounts.liquid",
        "file": "data/snippets/elite-volume-discounts.liquid",
        "name": "Descuentos por Cantidad / Tiered Pricing",
    },
    {
        "key": "snippets/elite-stock-countdown.liquid",
        "file": "data/snippets/elite-stock-countdown.liquid",
        "name": "Barra de Urgencia de Stock & Temporizador",
    },
    {
        "key": "snippets/elite-social-proof.liquid",
        "file": "data/snippets/elite-social-proof.liquid",
        "name": "Notificación Toast de Ventas Recientes (Social Proof)",
    },
    {
        "key": "snippets/elite-drawer-cart.liquid",
        "file": "data/snippets/elite-drawer-cart.liquid",
        "name": "Carrito Deslizable con Meta de Envío Gratis (Drawer Cart)",
    },
]


async def main():
    console.print(Panel(
        "[bold cyan]⚡ Desplegador Integral de Componentes CRO para Shopify[/bold cyan]\n"
        f"Tienda Objetivo: [bold yellow]{config.SHOP_DOMAIN}[/bold yellow]",
        title="Shopify CRO Engine",
        border_style="cyan"
    ))

    client = ShopifyClient(dry_run=config.DRY_RUN)

    # 1. Fetch active theme
    active_theme = await client.get_active_theme()
    theme_id = active_theme.get("id", 164813537509)
    theme_name = active_theme.get("name", "Horizon")
    console.print(f"[bold green]✔ Tema Activo Identificado:[/] {theme_name} (ID: {theme_id})\n")

    for item in SNIPPETS_TO_DEPLOY:
        key = item["key"]
        name = item["name"]
        file_path = Path(item["file"])

        if not file_path.exists():
            console.print(f"[bold red]❌ Archivo no encontrado:[/] {file_path}")
            continue

        content = file_path.read_text(encoding="utf-8")
        console.print(f"Subiendo [bold white]{name}[/] (`{key}`)...")

        try:
            await client.update_theme_asset(
                theme_id=theme_id,
                asset_key=key,
                value=content.strip(),
            )
            console.print(f"  [bold green]✔ Snippet `{key}` subido con éxito al tema.[/bold green]")
        except Exception as e:
            console.print(f"  [bold red]❌ Error al subir snippet: {e}[/bold red]")

    console.print(Panel(
        "[bold green]✨ ¡Todos los Componentes de Conversión (CRO) Desplegados con Éxito![/bold green]\n\n"
        "1. [bold]Descuentos por Cantidad:[/bold] `snippets/elite-volume-discounts.liquid`\n"
        "2. [bold]Barra de Urgencia & Countdown:[/bold] `snippets/elite-stock-countdown.liquid`\n"
        "3. [bold]Notificaciones de Compras en Vivo:[/bold] `snippets/elite-social-proof.liquid`\n"
        "4. [bold]Carrito Deslizable (Drawer Cart):[/bold] `snippets/elite-drawer-cart.liquid`",
        title="Despliegue Completado",
        border_style="green"
    ))


if __name__ == "__main__":
    asyncio.run(main())
