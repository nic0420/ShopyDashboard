"""
Main CLI Runner for the Shopify Multi-Agent Dropshipping Pipeline.
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich import print as rprint

from config import config
from tools.shopify_client import ShopifyClient
from tools.image_generator import ImageGeneratorTool
from agents.orchestrator import DropshippingPipelineOrchestrator
from utils.csv_parser import parse_csv

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Setup rich console
console = Console(force_terminal=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
# Silence httpx verbose logs for clean CLI display
logging.getLogger("httpx").setLevel(logging.WARNING)


def display_welcome_banner():
    banner = """
  ╔═══════════════════════════════════════════════════════════════╗
  ║       🛍️  SHOPIFY MULTI-AGENT DROPSHIPPING PIPELINE          ║
  ║  Catalog Agent ➔ Art Agent ➔ Frontend Liquid Coder Agent       ║
  ║  Target Store: da6gne-6x.myshopify.com                        ║
  ╚═══════════════════════════════════════════════════════════════╝
    """
    console.print(f"[bold cyan]{banner}[/bold cyan]")


def display_pipeline_summary(report):
    # Summary Table
    table = Table(title="🚀 Resumen de Ejecución del Pipeline", show_header=True, header_style="bold magenta")
    table.add_column("Módulo / Agente", style="cyan", width=25)
    table.add_column("Resultado Clave", style="green")
    table.add_column("Estado", style="bold yellow", justify="center")

    table.add_row(
        "Tool de Conexión",
        f"Shopify OAuth 2.0 API ({config.SHOP_DOMAIN}) | Scopes: 8 activos",
        "✔ Conectado",
    )
    table.add_row(
        "Agente de Catálogo",
        f"SEO Title: '{report.catalog_result.optimized_seo_title}'\nPrecio: ${report.catalog_result.suggested_price} (Compare: ${report.catalog_result.compare_at_price})\nBeneficios: {len(report.catalog_result.benefits)} generados",
        "✔ Completado",
    )
    table.add_row(
        "Agente de Arte",
        f"Assets en CDN: {len(report.art_result.assets)} imágenes\nCDN Principal: {report.art_result.primary_cdn_url[:48]}...",
        "✔ Completado",
    )
    table.add_row(
        "Agente Frontend (Liquid)",
        f"Snippet: {report.frontend_result.liquid_snippet_key}\nTemplate: {report.frontend_result.template_json_key}\nTema ID: {report.frontend_result.theme_id}",
        "✔ Completado",
    )

    console.print(table)

    # Detailed Tree View of Artifacts
    tree = Tree("📦 [bold blue]Ecosistema de Assets Generados e Inyectados[/bold blue]")
    
    cat_node = tree.add("📑 [bold cyan]Agente de Catálogo[/bold cyan]")
    cat_node.add(f"Título Original: [dim]{report.catalog_result.original_title}[/dim]")
    cat_node.add(f"Título Optimizado SEO: [bold green]{report.catalog_result.optimized_seo_title}[/bold green]")
    prod_id = str(report.catalog_result.shopify_product_id or "")
    cat_node.add(f"Shopify Product ID: [yellow]{prod_id}[/yellow]")
    if prod_id:
        clean_num_id = prod_id.split("/")[-1]
        store_slug = config.SHOP_DOMAIN.replace(".myshopify.com", "")
        admin_url = f"https://admin.shopify.com/store/{store_slug}/products/{clean_num_id}"
        legacy_admin_url = f"https://{config.SHOP_DOMAIN}/admin/products/{clean_num_id}"
        cat_node.add(f"🔗 [bold green]Admin Direct URL:[/] [link={admin_url}]{admin_url}[/link]")
    
    art_node = tree.add("🎨 [bold purple]Agente de Arte (Shopify CDN)[/bold purple]")
    for asset in report.art_result.assets:
        art_node.add(f"[{asset.asset_type}] ➔ [link={asset.cdn_url}]{asset.cdn_url}[/link]")

    liq_node = tree.add("💻 [bold orange3]Agente Frontend (Liquid Coder)[/bold orange3]")
    for mod in report.frontend_result.modified_assets:
        liq_node.add(f"[bold]{mod.asset_key}[/bold] ({mod.action}) ➔ {mod.content_summary}")

    console.print(Panel(tree, border_style="blue", title="Estructura Multi-Agente"))
    console.print(f"\n[bold green]✨ Tiempo total de ejecución:[/] {report.execution_time_sec} segundos\n")


async def main():
    parser = argparse.ArgumentParser(description="Shopify Multi-Agent Dropshipping Pipeline")
    parser.add_argument(
        "--input",
        type=str,
        default="data/catalogo_proveedor.csv",
        help="Path to supplier CSV or JSON payload",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Run in Sandbox / Simulation mode without modifying live store",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run in Live Mode targeting da6gne-6x.myshopify.com",
    )
    parser.add_argument(
        "--oauth-url",
        action="store_true",
        help="Print the OAuth 2.0 authorization URL for the Shopify store",
    )
    parser.add_argument(
        "--exchange-code",
        type=str,
        default=None,
        help="Exchange Shopify OAuth authorization code or callback URL for permanent access token",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save execution JSON report",
    )

    args = parser.parse_args()

    display_welcome_banner()

    is_dry_run = not args.live if args.live else args.dry_run

    # Initialize Shopify Client
    client = ShopifyClient(dry_run=is_dry_run)

    if args.oauth_url:
        auth_url = client.get_authorization_url()
        console.print(Panel(
            f"[bold yellow]URL de Autorización OAuth 2.0 de Shopify:[/bold yellow]\n\n[cyan]{auth_url}[/cyan]\n\n"
            f"[bold]Scopes solicitados:[/bold] {config.get_scopes_string()}\n"
            f"[bold]Client ID:[/bold] {config.CLIENT_ID}\n"
            f"[bold]Shop Domain:[/bold] {config.SHOP_DOMAIN}",
            title="OAuth 2.0 Auth Link",
            border_style="yellow"
        ))
        return

    if args.exchange_code:
        code = args.exchange_code.strip()
        if "code=" in code:
            import urllib.parse
            parsed = urllib.parse.urlparse(code)
            params = urllib.parse.parse_qs(parsed.query)
            code = params.get("code", [code])[0]
        console.print(f"[bold cyan]Intercambiando código OAuth por token permanente...[/bold cyan]")
        try:
            token_data = await client.exchange_code_for_token(code)
            access_token = token_data.get("access_token")
            console.print(f"[bold green]✔ Token obtenido con éxito:[/] {access_token}")
            env_path = Path(".env")
            if env_path.exists():
                content = env_path.read_text(encoding="utf-8")
                content = re.sub(r"SHOPIFY_ACCESS_TOKEN=.*", f"SHOPIFY_ACCESS_TOKEN={access_token}", content)
                env_path.write_text(content, encoding="utf-8")
                console.print("[bold green]✔ Variable SHOPIFY_ACCESS_TOKEN guardada automáticamente en .env[/bold green]")
        except Exception as e:
            console.print(f"[bold red]❌ Error al intercambiar código: {e}[/bold red]")
        return

    # Determine CSV / input path
    csv_file = args.input if (args.input and Path(args.input).exists()) else "data/catalogo_proveedor.csv"
    input_path = Path(csv_file)
    if not input_path.exists():
        console.print(f"[bold red]Error: Archivo de catálogo no encontrado en {input_path}[/bold red]")
        sys.exit(1)

    console.print(f"[bold]Modo de Ejecución:[/] {'[yellow]SANDBOX / DRY-RUN[/yellow]' if is_dry_run else '[green]PRODUCCIÓN (LIVE)[/green]'}")
    console.print(f"[bold]Tienda Objetivo:[/] {config.SHOP_DOMAIN}")
    console.print(f"[bold]Archivo de Catálogo Cargado:[/] [cyan]{input_path.name}[/cyan]\n")

    # Run Multi-Agent Orchestrator in Batch Mode
    orchestrator = DropshippingPipelineOrchestrator(shopify_client=client)
    successful_reports = []
    
    # Load batch items using parse_csv
    if str(input_path).endswith(".csv"):
        items = parse_csv(str(input_path))
    else:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            items = data if isinstance(data, list) else [data]

    total_items = len(items)
    console.print(f"[bold green]📦 Total de productos identificados en el lote:[/] {total_items}\n")

    for index, payload in enumerate(items, start=1):
        supplier_id = payload.get("supplier_id", f"ITEM-{index}")
        title = payload.get("raw_title", payload.get("title", "Unknown Product"))
        
        console.print(f"[bold magenta]───────────────────────────────────────────────────────────────[/bold magenta]")
        console.print(f"[bold cyan]▶ Ingesta Lote [{index}/{total_items}]:[/bold cyan] [bold]{supplier_id}[/bold] | {title[:60]}...")
        console.print(f"[bold magenta]───────────────────────────────────────────────────────────────[/bold magenta]")

        try:
            report = await orchestrator.run(payload)
            successful_reports.append(report)
            display_pipeline_summary(report)
        except Exception as e:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            error_line = f"[{timestamp}] [SUPPLIER_ID: {supplier_id}] [TITLE: {title}] Error: {type(e).__name__} - {str(e)}\n"
            logging.error(f"Fallo al procesar producto '{supplier_id}': {e}")
            with open("error_log.txt", "a", encoding="utf-8") as err_f:
                err_f.write(error_line)
            console.print(f"[bold red]❌ Error procesando {supplier_id}: {e}[/bold red]")
            console.print(f"[dim yellow]⚠ Error registrado en error_log.txt. Continuando con el siguiente artículo...[/dim yellow]\n")
            continue
        finally:
            # Pacing de API: pausa de 3 segundos para no saturar Rate Limit de Shopify
            if index < total_items:
                console.print(f"[dim blue]⏳ [Pacing API] Esperando 3 segundos antes del siguiente artículo...[/dim blue]\n")
                time.sleep(3)

    console.print(f"\n[bold green]🏁 Ingesta masiva finalizada. {len(successful_reports)} de {total_items} productos procesados con éxito.[/bold green]")

    if args.output and successful_reports:
        out_path = Path(args.output)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(json.dumps([r.model_dump() for r in successful_reports], indent=2, default=str))
        console.print(f"[bold green]✔ Reporte consolidado guardado en:[/] {out_path.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())
