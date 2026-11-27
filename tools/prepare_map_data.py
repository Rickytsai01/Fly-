#!/usr/bin/env python3
"""Prepare a Taiwan-wide simulator map from one or more georeferenced rasters.

DEM tiles are mosaicked directly into a compact simulator grid in EPSG:3826.
Land-cover rasters are sampled with nearest-neighbour resampling (categorical).
Building footprints are transformed into the same coordinate system.
World scale: 1 simulator unit = 10 metres.
"""
from __future__ import annotations
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.warp import reproject, transform_bounds
from pyproj import Transformer, CRS

TARGET_CRS = "EPSG:3826"  # TWD97 / TM2 zone 121
WORLD_METRES = 10.0
AIRPORTS = {
    "TPE": (25.0797, 121.2342),
    "RMQ": (24.2647, 120.6206),
    "HUN": (24.0237, 121.6169),
    "MZG": (23.5687, 119.6283),
    "TTT": (22.7549, 121.1017),
    "KHH": (22.5771, 120.3500),
}


def collect_files(explicit: list[str] | None, directory: str | None, suffixes: tuple[str, ...]) -> list[Path]:
    files: list[Path] = []
    for item in explicit or []:
        p = Path(item)
        if p.is_dir():
            files.extend(x for x in p.rglob("*") if x.is_file() and x.suffix.lower() in suffixes)
        elif p.is_file():
            files.append(p)
        else:
            raise FileNotFoundError(f"找不到輸入檔案：{p}")
    if directory:
        root = Path(directory)
        if not root.exists():
            raise FileNotFoundError(f"找不到資料夾：{root}")
        files.extend(x for x in root.rglob("*") if x.is_file() and x.suffix.lower() in suffixes)
    # Stable unique paths.
    return sorted(set(p.resolve() for p in files))


def raster_bounds_in_target(paths: list[Path]) -> tuple[float, float, float, float]:
    bounds = []
    for path in paths:
        with rasterio.open(path) as src:
            if src.crs is None:
                raise ValueError(f"Raster 沒有 CRS 座標系統：{path}")
            b = transform_bounds(src.crs, TARGET_CRS, *src.bounds, densify_pts=21)
            bounds.append(b)
    return (min(b[0] for b in bounds), min(b[1] for b in bounds),
            max(b[2] for b in bounds), max(b[3] for b in bounds))


def warp_mosaic(paths: list[Path], bounds: tuple[float, float, float, float],
                width: int, height: int, categorical: bool = False) -> tuple[np.ndarray, object]:
    west, south, east, north = bounds
    dst_transform = from_bounds(west, south, east, north, width, height)
    dst = np.full((height, width), np.nan, dtype=np.float32)
    method = Resampling.nearest if categorical else Resampling.bilinear
    for index, path in enumerate(paths, 1):
        print(f"處理圖幅 {index}/{len(paths)}：{path.name}")
        with rasterio.open(path) as src:
            if src.crs is None:
                raise ValueError(f"Raster 沒有 CRS 座標系統：{path}")
            reproject(
                source=rasterio.band(src, 1), destination=dst,
                src_transform=src.transform, src_crs=src.crs,
                src_nodata=src.nodata,
                dst_transform=dst_transform, dst_crs=TARGET_CRS,
                dst_nodata=np.nan, resampling=method,
                init_dest_nodata=False,
            )
    return dst, dst_transform


def sample_grid(grid: np.ndarray, bounds: tuple[float, float, float, float], x: float, y: float) -> float:
    west, south, east, north = bounds
    h, w = grid.shape
    col = (x - west) / (east - west) * (w - 1)
    row = (north - y) / (north - south) * (h - 1)
    if not (0 <= col <= w - 1 and 0 <= row <= h - 1):
        return 0.0
    c0, r0 = int(col), int(row)
    c1, r1 = min(w - 1, c0 + 1), min(h - 1, r0 + 1)
    fx, fy = col - c0, row - r0
    vals = [grid[r0, c0], grid[r0, c1], grid[r1, c0], grid[r1, c1]]
    if not all(np.isfinite(v) for v in vals):
        finite = [float(v) for v in vals if np.isfinite(v)]
        return float(np.mean(finite)) if finite else 0.0
    return float((1-fy)*((1-fx)*vals[0]+fx*vals[1]) + fy*((1-fx)*vals[2]+fx*vals[3]))


def read_buildings(paths: list[Path], bounds: tuple[float, float, float, float],
                   tpe_e: float, tpe_n: float, elev_grid: np.ndarray,
                   width: int, height: int, max_buildings: int) -> list[dict]:
    if not paths:
        return []
    import fiona
    from shapely.geometry import shape
    from shapely.ops import transform as shp_transform
    west, south, east, north = bounds
    to_target_default = Transformer.from_crs("EPSG:4326", TARGET_CRS, always_xy=True).transform
    result: list[dict] = []
    for path in paths:
        print(f"讀取建物：{path.name}")
        with fiona.open(path) as src:
            source_crs = src.crs_wkt or src.crs or "EPSG:4326"
            transformer = Transformer.from_crs(CRS.from_user_input(source_crs), TARGET_CRS, always_xy=True).transform
            for feat in src:
                if not feat.get("geometry"):
                    continue
                geom = shape(feat["geometry"])
                if geom.is_empty:
                    continue
                geom = shp_transform(transformer, geom)
                cx, cy = geom.centroid.x, geom.centroid.y
                if not (west <= cx <= east and south <= cy <= north):
                    continue
                minx, miny, maxx, maxy = geom.bounds
                props = feat.get("properties") or {}
                raw_h = props.get("height")
                levels = props.get("building:levels") or props.get("building_levels")
                try:
                    if raw_h not in (None, ""):
                        hgt = float(str(raw_h).lower().replace("m", "").strip())
                    elif levels not in (None, ""):
                        hgt = float(levels) * 3.2
                    else:
                        hgt = 8.5
                except (TypeError, ValueError):
                    hgt = 8.5
                ground = sample_grid(elev_grid, bounds, cx, cy) / WORLD_METRES
                result.append({
                    "x": (cx - tpe_e) / WORLD_METRES,
                    "z": (tpe_n - cy) / WORLD_METRES,
                    "w": max(2.5, (maxx - minx) / WORLD_METRES),
                    "d": max(2.5, (maxy - miny) / WORLD_METRES),
                    "h": max(3.0, min(180.0, hgt)),
                    "ground": max(0.0, ground),
                })
    if len(result) > max_buildings:
        step = math.ceil(len(result) / max_buildings)
        print(f"建物數量 {len(result):,}，為即時效能等距抽樣至約 {max_buildings:,} 筆")
        result = result[::step][:max_buildings]
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="合併台灣 DTM 圖幅並輸出飛行模擬器地圖 JSON")
    ap.add_argument("--dem", nargs="+", help="一個或多個 DEM/DTM GeoTIFF，也可傳入資料夾")
    ap.add_argument("--dem-dir", help="遞迴讀取此資料夾內所有 .tif/.tiff")
    ap.add_argument("--landcover", nargs="+", help="已重分類為 0–6 的土地覆蓋 GeoTIFF（類別使用最近鄰重採樣）")
    ap.add_argument("--landcover-dir", help="遞迴讀取土地覆蓋 GeoTIFF 資料夾")
    ap.add_argument("--buildings", nargs="+", help="建物 GeoJSON/GPKG/Shapefile 檔案")
    ap.add_argument("--buildings-dir", help="遞迴讀取建物資料夾中的 .geojson/.json/.gpkg/.shp")
    ap.add_argument("--out", default="data/taiwan-map.json")
    ap.add_argument("--width", type=int, default=640)
    ap.add_argument("--height", type=int, default=1600)
    ap.add_argument("--max-buildings", type=int, default=100000)
    args = ap.parse_args()

    dem_files = collect_files(args.dem, args.dem_dir, (".tif", ".tiff", ".vrt"))
    if not dem_files:
        ap.error("請提供 --dem 或 --dem-dir，且資料夾內必須有 GeoTIFF")
    if args.width < 100 or args.height < 100:
        ap.error("輸出網格至少需要 100 x 100")

    bounds = raster_bounds_in_target(dem_files)
    print(f"DTM 圖幅：{len(dem_files)} | TWD97 範圍：{bounds}")
    elev_grid, _ = warp_mosaic(dem_files, bounds, args.width, args.height, categorical=False)
    valid = np.isfinite(elev_grid)
    if not np.any(valid):
        raise RuntimeError("DTM 圖幅未覆蓋輸出範圍，沒有有效高程")

    # Clip only physically impossible negative land elevations/noise; retain coastal negative values as zero.
    valid_elev = elev_grid[valid]
    min_elev = float(np.nanmin(valid_elev))
    max_elev = float(np.nanmax(valid_elev))
    elevation = np.rint(np.nan_to_num(elev_grid, nan=0.0)).clip(-100, 5000).astype(np.int16)

    lc_files = collect_files(args.landcover, args.landcover_dir, (".tif", ".tiff", ".vrt"))
    landcover_grid = np.zeros((args.height, args.width), dtype=np.uint8)
    if lc_files:
        lc, _ = warp_mosaic(lc_files, bounds, args.width, args.height, categorical=True)
        # Inputs must already use the documented simulator legend 0..6.
        landcover_grid = np.nan_to_num(lc, nan=0).round().clip(0, 6).astype(np.uint8)
    landcover_grid[~valid] = 5  # outside DTM coverage is shown as water/unknown sea.

    tf = Transformer.from_crs("EPSG:4326", TARGET_CRS, always_xy=True)
    tpe_e, tpe_n = tf.transform(AIRPORTS["TPE"][1], AIRPORTS["TPE"][0])
    airport_out = []
    for code, (lat, lon) in AIRPORTS.items():
        e, n = tf.transform(lon, lat)
        airport_out.append({"code": code, "x": (e - tpe_e) / WORLD_METRES,
                            "z": (tpe_n - n) / WORLD_METRES,
                            "elevation": sample_grid(elev_grid, bounds, e, n)})

    building_files = collect_files(args.buildings, args.buildings_dir, (".geojson", ".json", ".gpkg", ".shp"))
    buildings = read_buildings(building_files, bounds, tpe_e, tpe_n, elev_grid,
                               args.width, args.height, args.max_buildings)

    west, south, east, north = bounds
    obj = {
        "schema": "tw-flightsim-map-v1",
        "metadata": {
            "dem": [p.name for p in dem_files],
            "crs": TARGET_CRS,
            "sourceResolution": "20m source recommended; resampled for real-time rendering",
            "demTileCount": len(dem_files),
            "landcoverTileCount": len(lc_files),
            "buildingCount": len(buildings),
            "gridResolutionApproxM": {
                "x": round((east - west) / args.width, 1),
                "y": round((north - south) / args.height, 1),
            },
            "note": "DTM elevations in metres; simulator local coordinates in 10m units. Map grid is downsampled; source DTM resolution is not preserved per vertex.",
        },
        "width": args.width,
        "height": args.height,
        "bounds": {
            "xMin": (west - tpe_e) / WORLD_METRES,
            "xMax": (east - tpe_e) / WORLD_METRES,
            "zMin": (tpe_n - north) / WORLD_METRES,
            "zMax": (tpe_n - south) / WORLD_METRES,
        },
        "minElevation": min_elev,
        "maxElevation": max_elev,
        "elevation": elevation.ravel().tolist(),
        "landcover": landcover_grid.ravel().tolist(),
        "airports": airport_out,
        "buildings": buildings,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    print(f"完成：{out} | {args.width}x{args.height} | DTM {len(dem_files)} 圖幅 | 建物 {len(buildings):,} 筆")
    print(f"網格約 {obj['metadata']['gridResolutionApproxM']['x']}m x {obj['metadata']['gridResolutionApproxM']['y']}m；原始 20m DTM 已為即時 3D 效能降採樣。")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        raise
