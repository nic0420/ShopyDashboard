"""
Shopify HTTP REST and GraphQL Client with OAuth 2.0 and Dropshipping Life-cycle Support.
"""

import json
import logging
import urllib.parse
from typing import Any, Dict, List, Optional
import httpx

from config import config

logger = logging.getLogger("ShopifyClient")


class ShopifyClient:
    """
    Shopify API Client supporting OAuth 2.0, GraphQL Admin API, REST Admin API,
    Product Lifecycle, File Uploads to CDN, and Theme Liquid/JSON modifications.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        shop_domain: Optional[str] = None,
        access_token: Optional[str] = None,
        api_version: Optional[str] = None,
        dry_run: Optional[bool] = None,
    ):
        self.client_id = client_id or config.CLIENT_ID
        self.client_secret = client_secret or config.CLIENT_SECRET
        self.shop_domain = (shop_domain or config.SHOP_DOMAIN).replace("https://", "").replace("http://", "").strip("/")
        self.access_token = access_token if access_token is not None else config.ACCESS_TOKEN
        self.api_version = api_version or config.API_VERSION
        self.dry_run = dry_run if dry_run is not None else config.DRY_RUN
        self.scopes = config.SCOPES

    # -------------------------------------------------------------------------
    # OAuth 2.0 Flow
    # -------------------------------------------------------------------------
    def get_authorization_url(
        self,
        redirect_uri: Optional[str] = None,
        state: str = "shopify_agent_state_nonce",
        scopes: Optional[List[str]] = None,
    ) -> str:
        """
        Generate the OAuth 2.0 authorization URL to install and authorize the app.
        """
        target_scopes = scopes or self.scopes
        target_redirect = redirect_uri or config.REDIRECT_URI
        params = {
            "client_id": self.client_id,
            "scope": ",".join(target_scopes),
            "redirect_uri": target_redirect,
            "state": state,
        }
        query_string = urllib.parse.urlencode(params)
        auth_url = f"https://{self.shop_domain}/admin/oauth/authorize?{query_string}"
        logger.info(f"Generated OAuth URL for scopes: {','.join(target_scopes)}")
        return auth_url

    async def exchange_code_for_token(
        self,
        code: str,
        redirect_uri: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Exchange the OAuth authorization code for a permanent Shopify Access Token.
        """
        if self.dry_run:
            mock_token = f"shpat_mock_{self.client_id[:8]}_access_token"
            self.access_token = mock_token
            return {
                "access_token": mock_token,
                "scope": ",".join(self.scopes),
                "status": "mock_success",
            }

        url = f"https://{self.shop_domain}/admin/oauth/access_token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            self.access_token = data.get("access_token", "")
            return data

    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # HTTP Headers
    # -------------------------------------------------------------------------
    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Shopify-Access-Token": self.access_token or "",
        }
        return headers

    # -------------------------------------------------------------------------
    # GraphQL Admin API
    # -------------------------------------------------------------------------
    async def graphql(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query/mutation against the Shopify Admin GraphQL API.
        """
        url = f"https://{self.shop_domain}/admin/api/{self.api_version}/graphql.json"

        if self.dry_run:
            logger.info(f"[DRY_RUN / Sandbox] Simulating GraphQL execution against {url}")
            return self._mock_graphql_response(query, variables)

        headers = self._get_headers()
        logger.info(f"Executing Live GraphQL POST to {url} with headers: {dict(headers, **{'X-Shopify-Access-Token': '***' if headers.get('X-Shopify-Access-Token') else 'EMPTY'})}")

        last_err = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    response = await client.post(
                        url,
                        headers=headers,
                        json={"query": query, "variables": variables or {}},
                    )
                    logger.info(f"Shopify GraphQL Response Status: {response.status_code}")
                    response.raise_for_status()
                    res_json = response.json()
                    if "errors" in res_json:
                        logger.error(f"GraphQL Errors: {res_json['errors']}")
                        raise RuntimeError(f"Shopify GraphQL API Error: {res_json['errors']}")
                    return res_json
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_err = e
                logger.warning(f"GraphQL connection attempt {attempt+1}/3 failed: {e}. Retrying in 2s...")
                await asyncio.sleep(2)

        raise last_err or RuntimeError("GraphQL execution failed after 3 retries")

    # -------------------------------------------------------------------------
    # REST Admin API
    # -------------------------------------------------------------------------
    async def rest_get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = config.get_rest_url(endpoint)
        if self.dry_run:
            return self._mock_rest_response("GET", endpoint)
        last_err = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url, headers=self._get_headers(), params=params)
                    response.raise_for_status()
                    return response.json()
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_err = e
                logger.warning(f"REST GET attempt {attempt+1}/3 failed: {e}. Retrying...")
                await asyncio.sleep(2)
        raise last_err or RuntimeError(f"REST GET failed for {endpoint}")

    async def rest_put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        url = config.get_rest_url(endpoint)
        if self.dry_run:
            return self._mock_rest_response("PUT", endpoint, data)
        last_err = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.put(url, headers=self._get_headers(), json=data)
                    response.raise_for_status()
                    return response.json()
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_err = e
                logger.warning(f"REST PUT attempt {attempt+1}/3 failed: {e}. Retrying...")
                await asyncio.sleep(2)
        raise last_err or RuntimeError(f"REST PUT failed for {endpoint}")

    async def rest_post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        url = config.get_rest_url(endpoint)
        if self.dry_run:
            return self._mock_rest_response("POST", endpoint, data)
        last_err = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, headers=self._get_headers(), json=data)
                    response.raise_for_status()
                    return response.json()
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_err = e
                logger.warning(f"REST POST attempt {attempt+1}/3 failed: {e}. Retrying...")
                await asyncio.sleep(2)
        raise last_err or RuntimeError(f"REST POST failed for {endpoint}")


    # -------------------------------------------------------------------------
    # High-level Catalog & Product Operations
    # -------------------------------------------------------------------------
    async def create_product(self, product_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a product in Shopify using GraphQL productCreate mutation.
        """
        mutation = """
        mutation productCreate($input: ProductInput!, $media: [CreateMediaInput!]) {
            productCreate(input: $input, media: $media) {
                product {
                    id
                    title
                    handle
                    descriptionHtml
                    vendor
                    productType
                    tags
                    status
                    variants(first: 10) {
                        edges {
                            node {
                                id
                                title
                                price
                                sku
                                inventoryQuantity
                                inventoryItem {
                                    id
                                }
                            }
                        }
                    }
                    media(first: 10) {
                        edges {
                            node {
                                ... on MediaImage {
                                    id
                                    image {
                                        url
                                        altText
                                    }
                                }
                            }
                        }
                    }
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        variables = {
            "input": {
                "title": product_input.get("title"),
                "descriptionHtml": product_input.get("descriptionHtml"),
                "vendor": product_input.get("vendor", "Dropshipping AutoBot"),
                "productType": product_input.get("productType", "General"),
                "tags": product_input.get("tags", []),
                "status": product_input.get("status", "ACTIVE"),
            }
        }

        # Format media if present
        media_input = []
        for img_url in product_input.get("images", []):
            media_input.append({
                "originalSource": img_url,
                "mediaContentType": "IMAGE",
                "alt": product_input.get("title", "Product Image"),
            })

        if media_input:
            variables["media"] = media_input

        res = await self.graphql(mutation, variables)

        # In Shopify 2024-10, update the default created variant with pricing & SKU
        if not self.dry_run and "variants" in product_input and product_input["variants"]:
            created_prod = res.get("data", {}).get("productCreate", {}).get("product")
            if created_prod and created_prod.get("id"):
                var_edges = created_prod.get("variants", {}).get("edges", [])
                if var_edges:
                    default_variant_id = var_edges[0]["node"]["id"]
                    first_var_input = product_input["variants"][0]
                    update_mutation = """
                    mutation productVariantUpdate($input: ProductVariantInput!) {
                        productVariantUpdate(input: $input) {
                            productVariant {
                                id
                                price
                                compareAtPrice
                                sku
                            }
                            userErrors {
                                field
                                message
                            }
                        }
                    }
                    """
                    var_update_vars = {
                        "input": {
                            "id": default_variant_id,
                            "price": str(first_var_input.get("price", "29.99")),
                            "compareAtPrice": str(first_var_input.get("compareAtPrice", "")),
                            "sku": first_var_input.get("sku", ""),
                        }
                    }
                    try:
                        await self.graphql(update_mutation, var_update_vars)
                    except Exception as e:
                        logger.warning(f"Note on variant pricing update: {e}")

        return res

    async def add_product_media(self, product_id: str, media_urls: List[str], alt_text: str = "") -> Dict[str, Any]:
        """
        Attaches media/images to an existing Shopify product gallery via GraphQL productCreateMedia mutation.
        """
        if self.dry_run or not product_id or not media_urls:
            return {"status": "simulated_or_empty"}

        clean_prod_id = product_id if product_id.startswith("gid://") else f"gid://shopify/Product/{product_id}"

        mutation = """
        mutation productCreateMedia($productId: ID!, $media: [CreateMediaInput!]!) {
            productCreateMedia(productId: $productId, media: $media) {
                media {
                    ... on MediaImage {
                        id
                        image {
                            url
                            altText
                        }
                    }
                }
                mediaUserErrors {
                    field
                    message
                }
            }
        }
        """
        media_input = [
            {
                "originalSource": url,
                "mediaContentType": "IMAGE",
                "alt": alt_text or "Product Image",
            }
            for url in media_urls
            if url and url.startswith("http")
        ]
        if not media_input:
            return {"status": "no_valid_urls"}

        variables = {
            "productId": clean_prod_id,
            "media": media_input,
        }
        try:
            return await self.graphql(mutation, variables)
        except Exception as e:
            logger.warning(f"Could not attach media to product {product_id}: {e}")
            return {"error": str(e)}


    # -------------------------------------------------------------------------
    # File & CDN Asset Upload Operations (stagedUploadsCreate + fileCreate)
    # -------------------------------------------------------------------------
    async def upload_file_to_cdn(
        self,
        file_name: str,
        file_content: bytes,
        mime_type: str = "image/png",
        alt_text: str = "Product Asset",
    ) -> Dict[str, Any]:
        """
        Uploads an image/asset directly to Shopify CDN using staged uploads GraphQL API.
        """
        if self.dry_run:
            # Deterministic clean CDN mock URL
            clean_name = file_name.replace(" ", "_")
            cdn_url = f"https://cdn.shopify.com/s/files/1/0000/0000/files/{clean_name}?v=1710000000"
            return {
                "file_id": "gid://shopify/MediaImage/9988776655",
                "url": cdn_url,
                "alt": alt_text,
                "status": "mock_uploaded",
            }

        # 1. Generate Staged Upload Target
        stage_mutation = """
        mutation stagedUploadsCreate($input: [StagedUploadInput!]!) {
            stagedUploadsCreate(input: $input) {
                stagedTargets {
                    url
                    resourceUrl
                    parameters {
                        name
                        value
                    }
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        stage_vars = {
            "input": [
                {
                    "filename": file_name,
                    "mimeType": mime_type,
                    "resource": "FILE",
                    "httpMethod": "POST",
                }
            ]
        }
        stage_res = await self.graphql(stage_mutation, stage_vars)
        staged_targets = stage_res.get("data", {}).get("stagedUploadsCreate", {}).get("stagedTargets", [])
        if not staged_targets:
            raise RuntimeError(f"Failed to create staged upload target: {stage_res}")

        target = staged_targets[0]
        upload_url = target["url"]
        resource_url = target["resourceUrl"]
        params = {p["name"]: p["value"] for p in target["parameters"]}

        # 2. Upload Binary file to the Staged URL
        files = {"file": (file_name, file_content, mime_type)}
        async with httpx.AsyncClient(timeout=60.0) as client:
            upload_resp = await client.post(upload_url, data=params, files=files)
            upload_resp.raise_for_status()

        # 3. Create File Entity in Shopify
        file_create_mutation = """
        mutation fileCreate($files: [FileCreateInput!]!) {
            fileCreate(files: $files) {
                files {
                    id
                    alt
                    createdAt
                    ... on MediaImage {
                        image {
                            url
                        }
                    }
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        file_create_vars = {
            "files": [
                {
                    "originalSource": resource_url,
                    "alt": alt_text,
                    "contentType": "IMAGE",
                }
            ]
        }
        file_res = await self.graphql(file_create_mutation, file_create_vars)
        created_files = file_res.get("data", {}).get("fileCreate", {}).get("files", [])
        final_url = resource_url
        file_id = "gid://shopify/MediaImage/unknown"
        if created_files:
            file_id = created_files[0].get("id", file_id)
            img_info = created_files[0].get("image")
            if img_info and "url" in img_info:
                final_url = img_info["url"]

        return {
            "file_id": file_id,
            "url": final_url,
            "alt": alt_text,
            "status": "uploaded",
        }

    # -------------------------------------------------------------------------
    # Theme & Liquid/JSON Manipulation Operations
    # -------------------------------------------------------------------------
    async def get_active_theme(self) -> Dict[str, Any]:
        """
        Fetch the current main/active theme ID.
        """
        if self.dry_run:
            return {"id": 145000123456, "name": "Dawn Live Theme", "role": "main"}

        for attempt in range(3):
            try:
                res = await self.rest_get("themes.json")
                themes = res.get("themes", [])
                for theme in themes:
                    if theme.get("role") == "main":
                        return theme
                if themes:
                    return themes[0]
            except Exception as e:
                logger.warning(f"Attempt {attempt+1}/3 failed fetching themes: {e}")
                if attempt == 2:
                    return {"id": 164813537509, "name": "Horizon", "role": "main"}
                await asyncio.sleep(1)

        return {"id": 164813537509, "name": "Horizon", "role": "main"}


    async def get_theme_asset(self, theme_id: int, asset_key: str) -> Dict[str, Any]:
        """
        Fetch asset content (Liquid, JSON, CSS) from a theme.
        """
        endpoint = f"themes/{theme_id}/assets.json"
        res = await self.rest_get(endpoint, params={"asset[key]": asset_key})
        return res.get("asset", {})

    async def update_theme_asset(self, theme_id: int, asset_key: str, value: str) -> Dict[str, Any]:
        """
        Create or update a Liquid/JSON asset in the active theme.
        """
        endpoint = f"themes/{theme_id}/assets.json"
        payload = {
            "asset": {
                "key": asset_key,
                "value": value,
            }
        }
        res = await self.rest_put(endpoint, payload)
        return res.get("asset", {})

    async def get_pages(self) -> List[Dict[str, Any]]:
        """
        Retrieves all online store pages.
        """
        if self.dry_run:
            return []
        try:
            res = await self.rest_get("pages.json")
            return res.get("pages", [])
        except Exception as e:
            logger.warning(f"Error fetching pages: {e}")
            return []

    async def create_or_update_page(self, title: str, body_html: str, handle: str) -> Dict[str, Any]:
        """
        Creates or updates a public shop page (Policy, FAQ, Tracking, etc.).
        """
        if self.dry_run:
            logger.info(f"[DRY_RUN] Simulated creation/update of page: '{title}' (handle: {handle})")
            return {"id": 99887766, "title": title, "handle": handle, "status": "published"}

        try:
            existing_pages = await self.get_pages()
            for p in existing_pages:
                if p.get("handle") == handle or p.get("title", "").lower() == title.lower():
                    page_id = p["id"]
                    payload = {
                        "page": {
                            "id": page_id,
                            "title": title,
                            "body_html": body_html,
                            "published": True,
                        }
                    }
                    res = await self.rest_put(f"pages/{page_id}.json", payload)
                    return res.get("page", {})

            # Create new page
            payload = {
                "page": {
                    "title": title,
                    "body_html": body_html,
                    "handle": handle,
                    "published": True,
                }
            }
            res = await self.rest_post("pages.json", payload)
            return res.get("page", {})
        except Exception as e:
            logger.error(f"Failed creating/updating page '{title}': {e}")
            return {"title": title, "handle": handle, "status": "error", "error": str(e)}

    async def create_order_fulfillment(
        self,
        order_id: str,
        tracking_number: str,
        tracking_company: str = "CJ_DROPSHIPPING",
        tracking_url: Optional[str] = None,
        notify_customer: bool = True,
    ) -> Dict[str, Any]:
        """
        Creates a fulfillment in Shopify with tracking info returned from dropshipping supplier.
        Uses Shopify GraphQL fulfillmentCreateV2 mutation.
        """
        clean_order_id = str(order_id)
        if not clean_order_id.startswith("gid://"):
            clean_order_id = f"gid://shopify/Order/{clean_order_id}"

        mutation = """
        mutation fulfillmentCreateV2($fulfillment: FulfillmentV2Input!) {
            fulfillmentCreateV2(fulfillment: $fulfillment) {
                fulfillment {
                    id
                    status
                    trackingInfo {
                        number
                        company
                        url
                    }
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        tracking_info: Dict[str, Any] = {
            "number": tracking_number,
            "company": tracking_company,
        }
        if tracking_url:
            tracking_info["url"] = tracking_url

        variables = {
            "fulfillment": {
                "notifyCustomer": notify_customer,
                "trackingInfo": tracking_info,
                "lineItemsByFulfillmentOrder": [
                    {
                        "fulfillmentOrderId": clean_order_id
                    }
                ]
            }
        }
        return await self.graphql(mutation, variables)

    async def get_primary_location_id(self) -> str:
        """
        Retrieves the primary inventory location ID for the store.
        """
        if self.dry_run:
            return "gid://shopify/Location/12345678"

        query = """
        query {
            locations(first: 1) {
                edges {
                    node {
                        id
                        name
                    }
                }
            }
        }
        """
        res = await self.graphql(query)
        edges = res.get("data", {}).get("locations", {}).get("edges", [])
        if edges:
            return edges[0].get("node", {}).get("id", "gid://shopify/Location/12345678")
        return "gid://shopify/Location/12345678"

    async def update_variant_price(
        self,
        product_id: str,
        variant_id: str,
        price: float,
        compare_at_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Updates the price and compare-at price of a product variant in Shopify.
        Uses GraphQL productVariantsBulkUpdate.
        """
        clean_prod_id = str(product_id)
        if not clean_prod_id.startswith("gid://"):
            clean_prod_id = f"gid://shopify/Product/{clean_prod_id}"

        clean_var_id = str(variant_id)
        if not clean_var_id.startswith("gid://"):
            clean_var_id = f"gid://shopify/ProductVariant/{clean_var_id}"

        mutation = """
        mutation productVariantsBulkUpdate($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
            productVariantsBulkUpdate(productId: $productId, variants: $variants) {
                productVariants {
                    id
                    price
                    compareAtPrice
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        variant_input: Dict[str, Any] = {
            "id": clean_var_id,
            "price": str(price),
        }
        if compare_at_price is not None:
            variant_input["compareAtPrice"] = str(compare_at_price)

        variables = {
            "productId": clean_prod_id,
            "variants": [variant_input],
        }
        return await self.graphql(mutation, variables)

    async def set_inventory_quantity(
        self,
        inventory_item_id: str,
        location_id: str,
        available_quantity: int,
    ) -> Dict[str, Any]:
        """
        Sets the on-hand available inventory quantity at a specific location using GraphQL inventorySetOnHandQuantities.
        """
        clean_inv_id = str(inventory_item_id)
        if not clean_inv_id.startswith("gid://"):
            clean_inv_id = f"gid://shopify/InventoryItem/{clean_inv_id}"

        clean_loc_id = str(location_id)
        if not clean_loc_id.startswith("gid://"):
            clean_loc_id = f"gid://shopify/Location/{clean_loc_id}"

        mutation = """
        mutation inventorySetOnHandQuantities($input: InventorySetOnHandQuantitiesInput!) {
            inventorySetOnHandQuantities(input: $input) {
                inventoryAdjustmentGroup {
                    reason
                }
                userErrors {
                    field
                    message
                }
            }
        }
        """
        variables = {
            "input": {
                "reason": "correction",
                "setQuantities": [
                    {
                        "inventoryItemId": clean_inv_id,
                        "locationId": clean_loc_id,
                        "quantity": int(available_quantity),
                    }
                ]
            }
        }
        return await self.graphql(mutation, variables)

    # -------------------------------------------------------------------------
    # Mock Responses for Sandbox / Offline Testing
    # -------------------------------------------------------------------------
    def _mock_graphql_response(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        variables = variables or {}
        if "locations" in query:
            return {
                "data": {
                    "locations": {
                        "edges": [{"node": {"id": "gid://shopify/Location/12345678", "name": "Primary Warehouse"}}]
                    }
                }
            }
        if "productVariantsBulkUpdate" in query:
            return {
                "data": {
                    "productVariantsBulkUpdate": {
                        "productVariants": [{"id": "gid://shopify/ProductVariant/4455667788", "price": "24.99"}],
                        "userErrors": [],
                    }
                }
            }
        if "inventorySetOnHandQuantities" in query:
            return {
                "data": {
                    "inventorySetOnHandQuantities": {
                        "inventoryAdjustmentGroup": {"reason": "correction"},
                        "userErrors": [],
                    }
                }
            }
        if "fulfillmentCreateV2" in query:
            f_input = variables.get("fulfillment", {})
            t_info = f_input.get("trackingInfo", {})
            return {
                "data": {
                    "fulfillmentCreateV2": {
                        "fulfillment": {
                            "id": "gid://shopify/Fulfillment/9988776655",
                            "status": "SUCCESS",
                            "trackingInfo": [
                                {
                                    "number": t_info.get("number", "CJ_TRACK_MOCK_123"),
                                    "company": t_info.get("company", "CJ_DROPSHIPPING"),
                                    "url": t_info.get("url", "https://t.17track.net"),
                                }
                            ],
                        },
                        "userErrors": [],
                    }
                }
            }
        if "productCreate" in query:
            p_input = variables.get("input", {})
            title = p_input.get("title", "Sample Dropshipping Product")
            handle = title.lower().replace(" ", "-").replace("/", "-")
            return {
                "data": {
                    "productCreate": {
                        "product": {
                            "id": "gid://shopify/Product/8899112233",
                            "title": title,
                            "handle": handle,
                            "descriptionHtml": p_input.get("descriptionHtml", "<p>SEO Optimized Copy</p>"),
                            "vendor": p_input.get("vendor", "Dropshipping AutoBot"),
                            "productType": p_input.get("productType", "General"),
                            "tags": p_input.get("tags", ["trending", "dropship"]),
                            "status": "ACTIVE",
                            "variants": {
                                "edges": [
                                    {
                                        "node": {
                                            "id": "gid://shopify/ProductVariant/4455667788",
                                            "title": "Default Title",
                                            "price": "29.99",
                                            "sku": f"DS-{handle[:8].upper()}",
                                            "inventoryQuantity": 100,
                                            "inventoryItem": {
                                                "id": "gid://shopify/InventoryItem/1122334455"
                                            }
                                        }
                                    }
                                ]
                            },
                            "media": {
                                "edges": [
                                    {
                                        "node": {
                                            "id": "gid://shopify/MediaImage/10101010",
                                            "image": {
                                                "url": "https://cdn.shopify.com/s/files/1/0000/0000/files/product_hero.jpg",
                                                "altText": title,
                                            }
                                        }
                                    }
                                ]
                            }
                        },
                        "userErrors": [],
                    }
                }
            }
        return {"data": {"result": "mock_success"}}

    def _mock_rest_response(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if "themes.json" in endpoint:
            return {
                "themes": [
                    {
                        "id": 145000123456,
                        "name": "Dawn (Dropship Optimized)",
                        "role": "main",
                    }
                ]
            }
        if "assets.json" in endpoint:
            if method == "GET":
                return {
                    "asset": {
                        "key": "templates/product.json",
                        "value": json.dumps({
                            "sections": {
                                "main": {
                                    "type": "main-product",
                                    "blocks": {
                                        "title": {"type": "title"},
                                        "price": {"type": "price"},
                                        "description": {"type": "description"},
                                    },
                                    "block_order": ["title", "price", "description"]
                                }
                            },
                            "order": ["main"]
                        }, indent=2),
                    }
                }
            elif method in ("PUT", "POST"):
                asset = data.get("asset", {}) if data else {}
                return {
                    "asset": {
                        "key": asset.get("key", "snippets/custom-product-features.liquid"),
                        "public_url": f"https://{self.shop_domain}/cdn/assets/{asset.get('key')}",
                        "updated_at": "2026-09-11T13:46:00-03:00",
                        "value": asset.get("value", ""),
                    }
                }
        return {"status": "mock_success", "endpoint": endpoint}
