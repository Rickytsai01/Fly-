#!/usr/bin/env python3
"""Integrity and source-sample verification for the 20 m browser terrain tiles."""
import json, random, sys
from pathlib import Path
import numpy as np
import rasterio

def main():
    root=Path(sys.argv[1] if len(sys.argv)>1 else 'data/terrain20m')
    dem=Path(sys.argv[2]) if len(sys.argv)>2 else None
    idx=json.loads((root/'index.json').read_text(encoding='utf-8'))
    ts=idx['tileSize']; records={(t['r'],t['c']):t for t in idx['tiles']}
    assert idx['schema']=='tw-flightsim-terrain-tiles-v1' and len(records)==idx['tileCount']
    for t in idx['tiles']:
        p=root/t['file']; assert p.is_file() and p.stat().st_size==ts*ts*2, p
    print(f'PASS: {len(records)} tiles, all binary sizes correct')
    if dem:
        rng=random.Random(20261126)
        with rasterio.open(dem) as ds:
            for _ in range(100):
                t=rng.choice(idx['tiles']); rr=rng.randrange(t['h']); cc=rng.randrange(t['w'])
                tile=np.fromfile(root/t['file'],dtype='<i2').reshape(ts,ts)
                got=int(tile[rr,cc]); raw=ds.read(1,window=((t['r']*ts+rr,t['r']*ts+rr+1),(t['c']*ts+cc,t['c']*ts+cc+1)))[0,0]
                expected=-32767 if raw==ds.nodata or not np.isfinite(raw) else int(np.clip(np.rint(raw),-100,5000))
                assert got==expected,(t['file'],rr,cc,got,expected)
        print('PASS: 100 random tile samples match the source GeoTIFF')
if __name__=='__main__': main()
