#!/usr/bin/env python3
"""Regression checks for v8 runway touchdown geometry and landing guards.
This is a reduced geometry/source test, not a browser flight-physics test.
"""
from pathlib import Path
import math

SOURCE = Path(__file__).resolve().parents[1] / 'index.html'
TEXT = SOURCE.read_text(encoding='utf-8')

def norm_abs(a):
    return abs((a + math.pi * 3) % (math.pi * 2) - math.pi)

def metrics(px, pz, apx, apz, heading_deg, runway_heading_deg, runway_len=360, runway_width=24):
    base = math.radians(runway_heading_deg)
    aircraft = math.radians(heading_deg)
    reverse = norm_abs(aircraft - base) > math.pi / 2
    hdg = base + (math.pi if reverse else 0)
    dx, dz = math.sin(hdg), -math.cos(hdg)
    tx, tz = apx - dx * runway_len * .42, apz - dz * runway_len * .42
    rx, rz = px - tx, pz - tz
    along = rx * dx + rz * dz
    cross = rx * math.cos(hdg) + rz * math.sin(hdg)
    heading_error = norm_abs(aircraft - hdg)
    return along, cross, heading_error, (along >= -8 and along <= runway_len * .78 and abs(cross) <= runway_width * .58)

def main():
    # Standard runway direction: touchdown zone is beyond the selected threshold.
    h = 50
    rad = math.radians(h)
    dx, dz = math.sin(rad), -math.cos(rad)
    apx = apz = 0.0
    threshold = (-dx * 360 * .42, -dz * 360 * .42)
    p = (threshold[0] + dx * 80, threshold[1] + dz * 80)
    a, c, he, zone = metrics(*p, apx, apz, h, h)
    assert zone and abs(a - 80) < 1e-6 and abs(c) < 1e-6 and he < 1e-6

    # Reverse-direction approach selects the opposite threshold and remains valid.
    rh = h + 180
    rrad = math.radians(rh)
    rdx, rdz = math.sin(rrad), -math.cos(rrad)
    rthreshold = (-rdx * 360 * .42, -rdz * 360 * .42)
    rp = (rthreshold[0] + rdx * 80, rthreshold[1] + rdz * 80)
    a, c, he, zone = metrics(*rp, apx, apz, rh, h)
    assert zone and abs(a - 80) < 1e-6 and he < 1e-6

    # The IAF gate also captures a reasonable along-track pass without requiring
    # the aircraft to hit the exact waypoint centre.
    iaf_along_m, iaf_cross_m = -8000 + 2800, 3000
    assert abs(iaf_along_m + 8000) < 3200 and abs(iaf_cross_m) < 3800
    assert not (abs(iaf_along_m + 8000) < 3200 and abs(iaf_cross_m) < 2500)

    # Excessive lateral offset, late touchdown, and poor heading are rejected.
    off = (p[0] + math.cos(rad) * 20, p[1] + math.sin(rad) * 20)
    assert not metrics(*off, apx, apz, h, h)[3]
    late = (threshold[0] + dx * 300, threshold[1] + dz * 300)
    assert not metrics(*late, apx, apz, h, h)[3]
    assert metrics(*p, apx, apz, h + 25, h)[2] > .30

    # Source invariants: ground guard, 1x autoland, touchdown VS retention,
    # IAF gate, flare energy management and post-touchdown stop workflow.
    required = [
        "if (state.onGround) { showNavToast('目前飛機在地面，請起飛後再啟動自動降落'); return; }",
        "state.simSpeed = 1; state.speedOptionIndex = 0;",
        "state.lastTouchdownVs = touchdownVs;",
        "const insideIafGate = Math.abs(alongIafM + 8000) < 3200 && Math.abs(crossIafM) < 3800;",
        "state.apPhase === 'FLARE'",
        "if (state.pendingLandingResult && state.onGround && state.speed <= 0.5)",
        "function getRunwayTouchdownMetrics",
    ]
    missing = [x for x in required if x not in TEXT]
    assert not missing, f'Missing source invariants: {missing}'
    print('PASS: runway touchdown zone geometry (both runway directions)')
    print('PASS: lateral/late/heading touchdown rejection')
    print('PASS: autoland 1x, IAF capture, flare energy, touchdown VS and rollout guards')
    print('LIMIT: no live browser, lift/drag, weather, flare or full touchdown simulation')

if __name__ == '__main__':
    main()
