# Expanded dictionary of common e-commerce count units and their clean singular display names
GENERIC_COUNT_UNITS = {
    "tier": "Tier",
    "tiers": "Tier",
    "shelf": "Shelf",
    "shelves": "Shelves",
    "door": "Door",
    "doors": "Door",
    "drawer": "Drawer",
    "drawers": "Drawer",
    "layer": "Layer",
    "layers": "Layer",
    "level": "Level",
    "levels": "Level",
    "pack": "Pack",
    "step": "Step",
    "steps": "Step",
    "bay": "Bay",
    "bays": "Bay",
    "tray": "Tray",
    "trays": "Tray",
}


def extract_generic_count_specs(slug_str):
    """Generically extracts specs like '4 Tier', '3 Door', '2 Drawer', '10 Pack', '5 Level' from any URL slug."""
    unit_pattern = "|".join(re.escape(u) for u in GENERIC_COUNT_UNITS.keys())

    # Matches patterns like '4-tier', '5 shelf', '3door', '2-drawers', '10pack', 'with-4-shelves'
    match = re.search(
        r"\b(\d+)\s*-?\s*(?:\w+)?\s*-?\s*(" + unit_pattern + r")\b",
        slug_str,
        re.IGNORECASE,
    )

    if match:
        count_num = match.group(1)
        raw_unit = match.group(2).lower()
        clean_unit = GENERIC_COUNT_UNITS.get(raw_unit, raw_unit.title())
        return f"{count_num} {clean_unit}"

    return ""
