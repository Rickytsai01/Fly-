#!/usr/bin/env python3
"""Download the public CSV resource index for MOI 2026 Taiwan 20m DTM and its linked files.

The government CSV is a resource catalogue; it may point to archives, rasters or tabular
point data. This helper downloads linked resources but does not silently convert unknown
formats. Inspect the downloaded file extensions and use QGIS to export source tiles to GeoTIFF
when necessary.
"""
from __future__ import annotations
import argparse
import csv
import io
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import urlparse, unquote

import requests

DEFAULT_INDEX = (
    "https://opdadm.moi.gov.tw/api/v1/no-auth/resource/api/dataset/"
    "B6219841-E247-4743-958D-77FB61067092/resource/"
    "D788C60B-33CB-4A84-A438-EC6E8B7060F1/download"
)
# The 2026 DTM dataset page currently exposes a resource whose display label says
# DSM. If its CSV has no explicit DTM rows, fall back to the clearly labelled 2025 DTM index.
FALLBACK_INDEX = (
    "https://opdadm.moi.gov.tw/api/v1/no-auth/resource/api/dataset/"
    "A964612F-0D64-4C81-BFE5-6C1F2BA61DED/resource/"
    "A0B94F67-8ADF-48A1-8DF0-C60719AD2B28/download"
)
URL_KEYS = ("url", "網址", "連結", "下載", "download", "link")
ALLOWED_EXT = {".zip", ".tif", ".tiff", ".csv", ".7z", ".rar", ".gz", ".gpkg", ".shp", ".geojson"}


def safe_name(value: str) -> str:
    value = re.sub(r"[\\/:*?\"<>|\s]+", "_", value.strip())
    return value[:100] or "dtm_resource"


def extract_links(text: str) -> list[tuple[str, str]]:
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    if not reader.fieldnames:
        raise ValueError("官方資源索引沒有可辨識的 CSV 標題列")
    url_fields = [f for f in reader.fieldnames if any(k in f.lower() for k in URL_KEYS)]
    if not url_fields:
        raise ValueError(f"找不到 URL 欄位；CSV 欄位為：{reader.fieldnames}")
    items = []
    for row in reader:
        title = next((str(row.get(k, "")).strip() for k in reader.fieldnames
                      if any(t in k.lower() for t in ("名稱", "name", "圖資")) and row.get(k)), "")
        # Never treat a DSM-only resource as a bare-earth DTM.
        type_fields = [f for f in reader.fieldnames if any(k in f.lower() for k in ("類型", "type"))]
        type_text = " ".join(str(row.get(k, "") or "") for k in type_fields).upper()
        row_text = (title + " " + type_text).upper()
        # DTM is bare-earth terrain; DSM includes buildings/vegetation. Prefer an
        # explicit DTM classification and never accidentally mix DSM into terrain.
        if "DSM" in row_text and "DTM" not in row_text:
            print(f"略過非 DTM 資源：{title or type_text}")
            continue
        if type_fields and "DTM" not in row_text:
            print(f"略過類型未明確標示 DTM 的資源：{title or type_text}")
            continue
        for field in url_fields:
            value = str(row.get(field, "")).strip()
            if value.startswith("http://") or value.startswith("https://"):
                items.append((title or field, value))
    # Stable deduplication.
    seen, unique = set(), []
    for title, url in items:
        if url not in seen:
            seen.add(url); unique.append((title, url))
    return unique


def main() -> None:
    ap = argparse.ArgumentParser(description="下載內政部 2026 台灣 20m DTM 資源索引與連結檔案")
    ap.add_argument("--out-dir", default="source_data/dem")
    ap.add_argument("--index-url", default=DEFAULT_INDEX)
    ap.add_argument("--fallback-index-url", default=FALLBACK_INDEX)
    ap.add_argument("--index-only", action="store_true", help="只下載 CSV 索引，不下載索引內的連結檔案")
    args = ap.parse_args()
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    headers={"User-Agent": "TaiwanFlightSimDataPrep/1.0"}
    print("取得內政部 2026 DTM 資源索引…")
    response = requests.get(args.index_url, timeout=(20, 120), headers=headers)
    response.raise_for_status()
    content = response.content
    text = response.content.decode(response.encoding or "utf-8-sig", errors="replace")
    index_path = out / "official_2026_dtm_resource_index.csv"
    index_path.write_bytes(content)
    print(f"索引已保存：{index_path}")
    if args.index_only:
        return
    links = extract_links(text)
    print(f"2026 索引中找到 {len(links)} 個明確 DTM 資料連結")
    if not links and args.fallback_index_url:
        print("2026 索引未找到明確 DTM 連結（頁面資源標籤目前顯示 DSM），改查官方 2025 DTM 索引…")
        fallback = requests.get(args.fallback_index_url, timeout=(20, 120), headers=headers)
        fallback.raise_for_status()
        fallback_content = fallback.content
        fallback_text = fallback.content.decode(fallback.encoding or "utf-8-sig", errors="replace")
        fallback_path = out / "official_2025_dtm_resource_index.csv"
        fallback_path.write_bytes(fallback_content)
        print(f"備援索引已保存：{fallback_path}")
        links = extract_links(fallback_text)
        print(f"2025 索引中找到 {len(links)} 個明確 DTM 資料連結")
    if not links:
        print("官方索引沒有可自動下載的明確 DTM 連結；請開啟 CSV 核對圖資類型及連結，勿將 DSM 當成裸地 DTM。")
        return
    for i, (title, url) in enumerate(links, 1):
        parsed = urlparse(url)
        ext = Path(unquote(parsed.path)).suffix.lower()
        if ext not in ALLOWED_EXT:
            ext = ".bin"
        base = safe_name(title or Path(unquote(parsed.path)).stem or f"dtm_{i:03d}")
        dest = out / f"{i:03d}_{base}{ext}"
        if dest.exists() and dest.stat().st_size > 0:
            print(f"[{i}/{len(links)}] 已存在，略過：{dest.name}")
            continue
        print(f"[{i}/{len(links)}] 下載：{title or url}")
        r = requests.get(url, stream=True, timeout=(20, 300), headers={"User-Agent": "TaiwanFlightSimDataPrep/1.0"})
        r.raise_for_status()
        ctype = r.headers.get("content-type", "").lower()
        if "text/html" in ctype:
            print("  跳過：連結回傳 HTML 網頁，可能需要平台登入或手動下載。")
            continue
        if ext == ".bin":
            if "zip" in ctype: dest = dest.with_suffix(".zip")
            elif "tiff" in ctype or "geotiff" in ctype: dest = dest.with_suffix(".tif")
            elif "csv" in ctype or "text/plain" in ctype: dest = dest.with_suffix(".csv")
        with dest.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk: f.write(chunk)
        print(f"  已保存：{dest.name} ({dest.stat().st_size:,} bytes)")
        if dest.suffix.lower() == ".zip":
            try:
                with zipfile.ZipFile(dest) as zf:
                    for member in zf.namelist():
                        if Path(member).suffix.lower() in {".tif", ".tiff"}:
                            zf.extract(member, out / "extracted")
                print("  已解壓 ZIP 內的 GeoTIFF 至 extracted 資料夾（若有）")
            except zipfile.BadZipFile:
                print("  注意：檔案副檔名為 ZIP，但內容不是有效 ZIP；請檢查來源連結。")
    print("下載流程結束。若得到 CSV 點位資料而非 GeoTIFF，請先用 QGIS 匯入並匯出為 EPSG:3826 GeoTIFF。")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"下載失敗：{exc}", file=sys.stderr)
        raise
