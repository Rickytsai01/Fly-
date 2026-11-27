#!/usr/bin/env python3
"""Regression test for the current runway-extension-line lateral guidance law.

This is intentionally a reduced 2-D kinematic model. It does NOT test lift,
energy management, vertical path, aircraft-specific physics, flare or touchdown.
"""
import math

def norm(a): return (a + math.pi) % (2 * math.pi) - math.pi

def run_case(start_bearing_deg, radius_world, heading_deg, speed_world_s=7.5):
    # Runway heading 000, runway centre (0,0), threshold at +151.2 world units.
    x = math.sin(math.radians(start_bearing_deg)) * radius_world
    z = -math.cos(math.radians(start_bearing_deg)) * radius_world
    heading = math.radians(heading_deg)
    roll = 0.0
    dt = 0.05
    threshold_z = 151.2
    for step in range(int(1800 / dt)):
        rel_x, rel_z = x, z - threshold_z
        along = -rel_z
        cross = rel_x
        aim_along = max(-1800, min(-180, along + max(650, abs(cross) * 0.75)))
        aim_x, aim_z = 0.0, threshold_z - aim_along
        target = math.atan2(aim_x - x, -(aim_z - z))
        error = norm(target - heading)
        desired_roll = max(-0.48, min(0.48, error * 1.45))
        roll += (desired_roll - roll) * (1 - math.exp(-4.5 * dt))
        heading += math.sin(roll) * 0.78 * dt
        x += math.sin(heading) * speed_world_s * dt
        z -= math.cos(heading) * speed_world_s * dt
        along_now = -(z - threshold_z)
        cross_now = x
        if -500 <= along_now <= 100 and abs(cross_now) < 100:
            return True, step * dt, along_now, cross_now
        if abs(x) > 10000 or abs(z) > 10000:
            break
    return False, step * dt, -(z - threshold_z), x

def main():
    cases = 0
    failures = []
    worst_time = 0.0
    for radius in (800, 1800, 2600):  # 8, 18, 26 km
        for bearing in range(0, 360, 15):
            for heading in range(0, 360, 45):
                cases += 1
                ok, elapsed, along, cross = run_case(bearing, radius, heading)
                worst_time = max(worst_time, elapsed)
                if not ok: failures.append((radius, bearing, heading, elapsed, along, cross))
    print(f'Cases: {cases}; captured: {cases-len(failures)}; failed: {len(failures)}; worst capture time: {worst_time:.1f}s')
    if failures:
        for f in failures[:20]: print('FAIL', f)
        raise SystemExit(1)
    print('PASS: all cases entered within 1 km cross-track and from 5 km before to 1 km after the threshold.')
    print('LIMIT: 2-D lateral guidance only; not a full flight-physics or landing test.')
if __name__ == '__main__': main()
