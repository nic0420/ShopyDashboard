# ShopyDashboard

Pipeline multi-agente en Python que automatiza el armado de una tienda de dropshipping en Shopify: toma el catálogo del proveedor, optimiza las fichas de producto, genera y sube imágenes, e inyecta componentes de conversión y páginas legales en el theme.

## Los agentes

| Agente | Qué hace |
|---|---|
| `catalog` | Lee el CSV del proveedor y optimiza títulos, descripciones y precios (SEO + margen) |
| `art` | Genera las imágenes de producto y las sube a Shopify |
| `liquid_coder` | Inyecta componentes Liquid de CRO y páginas legales en el theme |
| `fulfillment` | Maneja el flujo de pedidos |
| `orchestrator` | Coordina la corrida completa |
| `inventory_sync_worker` | Mantiene el stock sincronizado con el proveedor |

## Stack

- **Python** con FastAPI + uvicorn para la API y el dashboard
- **Shopify GraphQL Admin API** con OAuth2
- httpx, pydantic, rich, pyngrok
- Tests con pytest
- Dashboard web estático en `api/static/`
- Deploy en Vercel

## Cómo correrlo

```bash
git clone https://github.com/nic0420/ShopyDashboard.git
cd ShopyDashboard
pip install -r requirements.txt
uvicorn api.main:app --reload
```

Hace falta configurar las credenciales de la app de Shopify (OAuth2) en las variables de entorno antes de la primera corrida.

## Estado

Proyecto personal, en desarrollo.
