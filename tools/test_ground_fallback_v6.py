#!/usr/bin/env python3
"""Static regression checks for v6 terrain collision fallback and land-cover rendering."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
html = (root / "index.html").read_text(encoding="utf-8")

checks = {
    "procedural terrain collision function exists": "function getProceduralTerrainGroundHeightWorld(x,z)" in html,
    "missing/out-of-bounds map falls back to procedural terrain": "return getProceduralTerrainGroundHeightWorld(x,z);" in html,
    "real DTM sampling remains preferred": "if(Number.isFinite(detailed)) return detailed;" in html,
    "missing landcover is not interpreted as water": "const hasLandcover=Number(data.metadata?.landcoverTileCount||0)>0" in html,
    "vegetation requires a real landcover dataset": "Number(data.metadata?.landcoverTileCount||0)<=0" in html,
    "map-load failure gives an on-screen warning": "真實地形資料未載入，目前使用示意地形" in html,
}
for name, ok in checks.items():
    print(("PASS" if ok else "FAIL") + ": " + name)
if not all(checks.values()):
    raise SystemExit(1)
print(f"PASS: {len(checks)}/{len(checks)} static regression checks")
print("LIMIT: this does not replace browser physics, collision, or autoland testing.")
