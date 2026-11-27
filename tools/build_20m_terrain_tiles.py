#!/usr/bin/env python3
"""Split the supplied 20 m Taiwan elevation GeoTIFF into browser-streamable Int16 tiles."""
import argparse, json, math
from pathlib import Path
import numpy as np
import rasterio
from pyproj import Transformer

TILE=256
WORLD_METRES=10.0
TPE_LAT,TPE_LON=25.0797,121.2342

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--dem',required=True)
    ap.add_argument('--out',default='data/terrain20m')
    ap.add_argument('--tile-size',type=int,default=TILE)
    a=ap.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    tf=Transformer.from_crs('EPSG:4326','EPSG:3826',always_xy=True)
    tpe_e,tpe_n=tf.transform(TPE_LON,TPE_LAT)
    records=[]
    with rasterio.open(a.dem) as ds:
        if ds.count<1: raise RuntimeError('DEM has no raster band')
        ts=a.tile_size
        for r0 in range(0,ds.height,ts):
            for c0 in range(0,ds.width,ts):
                hh=min(ts,ds.height-r0); ww=min(ts,ds.width-c0)
                a0=ds.read(1,window=((r0,r0+hh),(c0,c0+ww)),masked=True)
                arr=np.asarray(a0.filled(-32767),dtype=np.float32)
                valid=np.isfinite(arr)&(arr!=-32767)
                if not valid.any(): continue
                arr=np.where(valid,np.clip(np.rint(arr),-100,5000),-32767).astype('<i2')
                # Pad edge tiles to a stable tile size; metadata keeps true dimensions.
                padded=np.full((ts,ts),-32767,dtype='<i2'); padded[:hh,:ww]=arr
                name=f'{r0//ts:03d}_{c0//ts:03d}.bin'
                (out/name).write_bytes(padded.tobytes(order='C'))
                # Raster sample centers: x=left+(col+.5)*20; y=top-(row+.5)*20
                west=ds.transform.c + (c0+0.5)*ds.transform.a
                north=ds.transform.f + (r0+0.5)*ds.transform.e
                x=(west-tpe_e)/WORLD_METRES
                z=(tpe_n-north)/WORLD_METRES
                records.append({'r':r0//ts,'c':c0//ts,'w':ww,'h':hh,'x':round(x,4),'z':round(z,4),'file':name})
        meta={'schema':'tw-flightsim-terrain-tiles-v1','tileSize':ts,'sampleSpacingM':20,'worldUnitsPerMetre':1/WORLD_METRES,'crs':'TWD97 / TM2 zone 121 (EPSG:3826)','source':Path(a.dem).name,'sourceWidth':ds.width,'sourceHeight':ds.height,'sourceBounds':[ds.bounds.left,ds.bounds.bottom,ds.bounds.right,ds.bounds.top],'originX':round((ds.bounds.left+10-tpe_e)/WORLD_METRES,4),'originZ':round((tpe_n-(ds.bounds.top-10))/WORLD_METRES,4),'nodata':-32767,'tileCount':len(records),'tiles':records}
    (out/'index.json').write_text(json.dumps(meta,separators=(',',':')),encoding='utf-8')
    print(f"Wrote {len(records)} tiles; {sum((out/t['file']).stat().st_size for t in records)/1e6:.1f} MB raw")
if __name__=='__main__': main()
