#!/usr/bin/env python3
"""
anonymize.py — Replace all real person names with fictional ones across
both prepared CSV datasets, then re-save them.

Covers:
  - prepared_products.csv  →  column `worker`
  - prepared_workers.csv   →  columns `employee_name`, `employee_id`, `equipment`

System/machine identifiers (USER01-USER50, AFRAME, DIHN, MKOC, SYSTEM, VVAH,
device IDs, hex equipment strings) are kept as-is since they are not personal.
"""

import hashlib
import re
from pathlib import Path

import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Fictional name pool — 450 unique gender-neutral / international names
# (more than the 414 unique workers + 2 employees we need to cover)
# ---------------------------------------------------------------------------
FICTIONAL_FIRST = [
    "Arin", "Bela", "Cato", "Dax", "Elio", "Fern", "Gale", "Hart", "Ivo",
    "Jade", "Kael", "Lark", "Miro", "Nova", "Orin", "Pike", "Quinn", "Rune",
    "Sage", "Tarn", "Ula", "Vale", "Wren", "Xen", "Yael", "Zev", "Alec",
    "Blair", "Cruz", "Drake", "Ember", "Flint", "Greer", "Haze", "Iris",
    "Joss", "Knox", "Lane", "Mars", "Neel", "Onyx", "Penn", "Reef", "Sky",
    "Tate", "Uri", "Voss", "Wade", "Xan", "Yuri", "Zara", "Axel", "Bryn",
    "Cleo", "Dune", "Esme", "Finn", "Glen", "Hugo", "Ines", "Juno", "Kira",
    "Lev", "Mace", "Nika", "Otto", "Pax", "Rho", "Sari", "Thea", "Uma",
    "Vera", "Wolf", "Zeke", "Ashe", "Bren", "Cole", "Dion", "Elan", "Faye",
    "Gray", "Hope", "Ivan", "Jace", "Koda", "Lux", "Mila", "Nash", "Opal",
    "Reed", "Shaw", "Teal", "Vex", "Wynn", "Zane", "Aster", "Blaze",
    "Cedar", "Delta", "Echo", "Frost", "Gwyn", "Heath", "Indigo",
]
FICTIONAL_LAST = [
    "Valen", "Thorne", "Wilder", "Frost", "Blackwood", "Sterling", "Marsh",
    "Rivers", "Stone", "Winters", "Ashford", "Drake", "Hawke", "Morrow",
    "Crane", "Lark", "Steel", "Moore", "Blake", "Fox", "Reed", "Pike",
    "Hart", "Cross", "Dunn", "West", "North", "East", "Finch", "Wolf",
    "Dale", "Brook", "Field", "Birch", "Elm", "Glen", "Holt", "Vale",
    "Ridge", "Peak", "Shore", "Cliff", "Banks", "Wells", "Hayes",
    "Grant", "Bell", "Snow", "Sage", "Clay", "Rowan", "Aspen", "Briar",
    "Cedar", "Slate", "Oak", "Fern", "Heath", "Ivy", "Alder", "Laurel",
    "Hazel", "Linden", "Maple", "Holly", "Gale", "Storm", "Rain", "Lake",
    "Pines", "Moss", "Dusk", "Dawn", "Crest", "Blaze", "Shard", "Flint",
    "Arrow", "Forge", "Basalt", "Quartz", "Cobalt", "Onyx", "Garnet",
    "Jasper", "Opal", "Coral", "Pearl", "Amber", "Raven", "Falcon",
    "Heron", "Osprey", "Wren", "Sparrow", "Swift", "Valor", "Noble",
    "Brave", "True", "Bright", "Keen", "Bold", "Stout",
]

# Names that are NOT personal — skip anonymization
SYSTEM_NAMES = {
    "AFRAME", "DIHN", "MKOC", "SYSTEM", "VVAH",
}
USER_PATTERN = re.compile(r"^USER\d+$")

def _is_system_name(name: str) -> bool:
    """Return True if name is a system/machine identifier, not a person."""
    if name in SYSTEM_NAMES:
        return True
    if USER_PATTERN.match(name):
        return True
    return False


def _build_name_map(real_names: list[str]) -> dict[str, str]:
    """
    Build a deterministic mapping from real names → fictional names.
    System/machine identifiers map to themselves.
    """
    # Sort personal names for deterministic ordering
    personal = sorted([n for n in real_names if not _is_system_name(n)])

    # Generate enough fictional combos, shuffled deterministically by hash
    combos = []
    for first in FICTIONAL_FIRST:
        for last in FICTIONAL_LAST:
            combos.append(f"{first} {last}")
    # Deterministic shuffle using hash-based sort
    combos.sort(key=lambda x: hashlib.md5(x.encode()).hexdigest())

    mapping = {}
    idx = 0
    for name in personal:
        mapping[name] = combos[idx % len(combos)]
        idx += 1

    # System names map to themselves
    for name in real_names:
        if _is_system_name(name):
            mapping[name] = name

    return mapping


def _build_employee_id_map(real_ids: list[str]) -> dict[str, str]:
    """Map real employee IDs to fictional ones."""
    fictional_ids = ["EMP_A", "EMP_B", "EMP_C", "EMP_D", "EMP_E", "EMP_F"]
    mapping = {}
    for i, rid in enumerate(sorted(real_ids)):
        mapping[rid] = fictional_ids[i % len(fictional_ids)]
    return mapping


def _build_equipment_map(real_equip: list[str], emp_id_map: dict) -> dict[str, str]:
    """
    Map equipment values that contain personal identifiers.
    Equipment like 'FAJBEL' or 'FAKKLA' embeds the employee ID.
    Hex strings and numeric IDs are not personal — leave as-is.
    """
    mapping = {}
    for eq in real_equip:
        replaced = False
        for real_id, fake_id in emp_id_map.items():
            if real_id in eq:
                mapping[eq] = eq.replace(real_id, fake_id)
                replaced = True
                break
        if not replaced:
            mapping[eq] = eq  # keep hex / numeric as-is
    return mapping


def anonymize() -> None:
    print("=" * 72)
    print("  Anonymisation — replacing real names with fictional ones")
    print("=" * 72)

    # --- Load datasets -------------------------------------------------------
    products = pd.read_csv(BASE_DIR / "prepared_products.csv", low_memory=False)
    workers = pd.read_csv(BASE_DIR / "prepared_workers.csv", low_memory=False)

    # --- Build unified name mapping ------------------------------------------
    all_real_names = sorted(
        set(products["worker"].unique().tolist()) |
        set(workers["employee_name"].unique().tolist())
    )
    name_map = _build_name_map(all_real_names)

    emp_id_map = _build_employee_id_map(list(workers["employee_id"].unique()))
    equip_map = _build_equipment_map(list(workers["equipment"].unique()), emp_id_map)

    print(f"  Personal names to anonymise: {sum(1 for n in all_real_names if not _is_system_name(n))}")
    print(f"  System identifiers kept:     {sum(1 for n in all_real_names if _is_system_name(n))}")
    print(f"  Employee IDs mapped:         {len(emp_id_map)}")
    print(f"  Equipment values mapped:     {sum(1 for k,v in equip_map.items() if k != v)}")

    # --- Apply to products ---------------------------------------------------
    products["worker"] = products["worker"].map(name_map)
    unmapped_prod = products["worker"].isna().sum()
    if unmapped_prod > 0:
        print(f"  ⚠ {unmapped_prod} unmapped product worker entries")

    # --- Apply to workers ----------------------------------------------------
    workers["employee_name"] = workers["employee_name"].map(name_map)
    workers["employee_id"] = workers["employee_id"].map(emp_id_map)
    workers["equipment"] = workers["equipment"].map(equip_map)

    unmapped_wrk = workers["employee_name"].isna().sum()
    if unmapped_wrk > 0:
        print(f"  ⚠ {unmapped_wrk} unmapped worker name entries")

    # Also check for names leaking into screen_heading
    if "screen_heading" in workers.columns:
        for real, fake in name_map.items():
            if _is_system_name(real):
                continue
            workers["screen_heading"] = workers["screen_heading"].fillna("").str.replace(
                real, fake, regex=False
            )
            workers["screen_heading"] = workers["screen_heading"].replace("", np.nan)

    # Also check json_text for embedded names
    if "json_text" in workers.columns:
        for real, fake in name_map.items():
            if _is_system_name(real):
                continue
            workers["json_text"] = workers["json_text"].fillna("").str.replace(
                real, fake, regex=False
            )
            workers["json_text"] = workers["json_text"].replace("", np.nan)

    # --- Save ----------------------------------------------------------------
    products.to_csv(BASE_DIR / "prepared_products.csv", index=False)
    workers.to_csv(BASE_DIR / "prepared_workers.csv", index=False)

    # Print sample mapping
    print("\n  Sample name mappings:")
    shown = 0
    for real, fake in sorted(name_map.items()):
        if not _is_system_name(real):
            print(f"    {real:45s} → {fake}")
            shown += 1
            if shown >= 15:
                print(f"    ... and {sum(1 for n in all_real_names if not _is_system_name(n)) - 15} more")
                break

    print(f"\n  Employee ID mappings:")
    for real, fake in emp_id_map.items():
        print(f"    {real} → {fake}")

    print(f"\n  ✓ Saved anonymised prepared_products.csv ({len(products):,} rows)")
    print(f"  ✓ Saved anonymised prepared_workers.csv  ({len(workers):,} rows)")
    print("=" * 72)


if __name__ == "__main__":
    anonymize()
