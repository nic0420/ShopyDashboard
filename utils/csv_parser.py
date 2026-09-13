"""
CSV Parser module for supplier dropshipping batch ingestion.
"""

import csv
import re
from pathlib import Path
from typing import Any, Dict, List, Union


def parse_csv(file_path: Union[str, Path] = "data/catalogo_proveedor.csv") -> List[Dict[str, Any]]:
    """
    Parses a supplier catalog CSV file using csv.DictReader and standardizes
    each row into a structured payload for multi-agent dropshipping processing.

    Expected standard keys:
    - supplier_id: str
    - raw_title: str
    - base_cost: float
    - raw_description: List[str]
    - reference_images: List[str]
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Supplier catalog CSV not found at: {path.resolve()}")

    standardized_records: List[Dict[str, Any]] = []

    with open(path, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            if not row or not any(row.values()):
                continue

            # 1. Supplier ID
            supplier_id = str(row.get("supplier_id") or row.get("id") or "UNKNOWN-SUPPLIER").strip()

            # 2. Raw Title
            raw_title = str(row.get("raw_title") or row.get("title") or "Generic Dropship Product").strip()

            # 3. Base Cost
            raw_cost = row.get("base_cost") or row.get("cost") or row.get("price") or 0.0
            try:
                # Remove any currency symbols ($/€/USD) if present
                clean_cost_str = re.sub(r"[^\d.]", "", str(raw_cost).replace(",", "."))
                base_cost = float(clean_cost_str) if clean_cost_str else 0.0
            except (ValueError, TypeError):
                base_cost = 0.0

            # 4. Raw Description (parse bullets by newlines, pipes or semicolons/commas)
            raw_desc_str = row.get("raw_description") or row.get("description") or row.get("features") or ""
            if isinstance(raw_desc_str, str):
                # Split by newline or pipe if present, otherwise split by comma if list-like
                if "\n" in raw_desc_str:
                    raw_description = [line.strip().lstrip("-•* ") for line in raw_desc_str.splitlines() if line.strip()]
                elif "|" in raw_desc_str:
                    raw_description = [item.strip() for item in raw_desc_str.split("|") if item.strip()]
                elif ";" in raw_desc_str:
                    raw_description = [item.strip() for item in raw_desc_str.split(";") if item.strip()]
                else:
                    raw_description = [item.strip() for item in raw_desc_str.split(",") if item.strip()]
            elif isinstance(raw_desc_str, list):
                raw_description = [str(x).strip() for x in raw_desc_str]
            else:
                raw_description = [str(raw_desc_str).strip()] if raw_desc_str else []

            # 5. Reference Images (comma-separated URLs to list)
            ref_images_str = row.get("reference_images") or row.get("images") or row.get("image_urls") or ""
            if isinstance(ref_images_str, str):
                reference_images = [img.strip() for img in re.split(r"[,;|\n]", ref_images_str) if img.strip() and img.strip().startswith("http")]
            elif isinstance(ref_images_str, list):
                reference_images = [str(img).strip() for img in ref_images_str if str(img).strip()]
            else:
                reference_images = []

            standardized_record: Dict[str, Any] = {
                "supplier_id": supplier_id,
                "raw_title": raw_title,
                "base_cost": base_cost,
                "raw_description": raw_description,
                "reference_images": reference_images,
                # Supporting extra optional columns if present
                "category": row.get("category", "Fitness & Training"),
                "product_type": row.get("product_type", "Functional Equipment"),
                "vendor": row.get("vendor", "ProFit Elite"),
            }

            standardized_records.append(standardized_record)

    return standardized_records
