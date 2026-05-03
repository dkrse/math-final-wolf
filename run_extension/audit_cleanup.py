"""
audit_cleanup.py — one-shot cleanup of notebooks 06-11:
  * strip cell outputs (stale, from a different machine)
  * remove trailing empty code cells
  * patch OUT_DIR `paper-rev-01/` -> `outputs/results/` in rev01 notebooks
  * reset execution_count

After cleanup the notebooks are ready for a clean re-execution.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS = [
    "06_bootstrap_ci.ipynb",
    "07_extended_to_1e12.ipynb",
    "08_missing_figures.ipynb",
    "09_rev01_alt_forms.ipynb",
    "10_rev01_robustness.ipynb",
    "11_rev01_m1_vs_m3.ipynb",
]

# OUT_DIR migration map
OUT_DIR_MIGRATIONS = {
    "WORK / 'paper-rev-01'": "WORK / 'outputs' / 'results'",
    "OUT_DIR = WORK / 'paper-rev-01'": "OUT_DIR = WORK / 'outputs' / 'results'",
    "OUT_DIR.mkdir(exist_ok=True)": "OUT_DIR.mkdir(parents=True, exist_ok=True)",
}


def strip_cell_outputs(cell: dict) -> bool:
    """True if the cell was modified."""
    changed = False
    if cell.get("cell_type") == "code":
        if cell.get("outputs"):
            cell["outputs"] = []
            changed = True
        if cell.get("execution_count") is not None:
            cell["execution_count"] = None
            changed = True
    return changed


def is_empty_code(cell: dict) -> bool:
    if cell.get("cell_type") != "code":
        return False
    src = cell.get("source", "")
    if isinstance(src, list):
        src = "".join(src)
    return not src.strip()


def patch_source(cell: dict, replacements: dict) -> bool:
    if cell.get("cell_type") != "code":
        return False
    src = cell.get("source", "")
    if isinstance(src, list):
        src_text = "".join(src)
    else:
        src_text = src
    new_text = src_text
    for old, new in replacements.items():
        new_text = new_text.replace(old, new)
    if new_text != src_text:
        # Re-split into lines preserving newlines (Jupyter convention)
        lines = new_text.splitlines(keepends=True)
        cell["source"] = lines
        return True
    return False


def main() -> None:
    summary = []
    for name in TARGETS:
        path = ROOT / name
        if not path.exists():
            print(f"  skip   {name} (not found)")
            continue
        nb = json.loads(path.read_text())
        n_outputs_stripped = 0
        n_empty_removed = 0
        n_outdir_patched = 0

        # 1. Strip outputs
        for cell in nb["cells"]:
            if strip_cell_outputs(cell):
                n_outputs_stripped += 1

        # 2. Remove trailing empty code cells (only at the end)
        while nb["cells"] and is_empty_code(nb["cells"][-1]):
            nb["cells"].pop()
            n_empty_removed += 1

        # 3. Patch OUT_DIR (only rev01 notebooks)
        if "rev01" in name:
            for cell in nb["cells"]:
                if patch_source(cell, OUT_DIR_MIGRATIONS):
                    n_outdir_patched += 1

        # Write back
        path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
        summary.append((name, n_outputs_stripped, n_empty_removed,
                        n_outdir_patched))
        print(f"  done   {name}: -{n_outputs_stripped} outputs, "
              f"-{n_empty_removed} empty cells, "
              f"+{n_outdir_patched} OUT_DIR patches")

    print("\n=== Summary ===")
    print(f"{'notebook':<32} {'-outputs':>9} {'-empty':>7} "
          f"{'OUT_DIR':>8}")
    for name, o, e, p in summary:
        print(f"{name:<32} {o:>9d} {e:>7d} {p:>8d}")


if __name__ == "__main__":
    main()
