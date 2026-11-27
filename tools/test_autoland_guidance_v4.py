#!/usr/bin/env python3
"""Reduced 2-D regression test for IAF capture and final centerline guidance.
Does not test aircraft lift, energy, vertical path, browser/WebGL, flare or touchdown."""
import math

def norm(a): return (a + math.pi) % (2 * math.pi) - math.pi

def run_case(bearing_deg, radius, heading_deg, speed=7.5):
    x = math.sin(math.radians(bearing_deg)) * radius
    z = -math.cos(math.radians(bearing_deg)) * radius
    # Mirror the simulator's runway-end selection: use the nearer runway end.
    runway_hdg = math.pi if z < 0 else 0.0
    dx, dz = math.sin(runway_hdg), -math.cos(runway_hdg)
    threshold_x, threshold_z = -dx * 151.2, -dz * 151.2
    iaf_x, iaf_z = threshold_x - dx * 800, threshold_z - dz * 800
    heading, roll = math.radians(heading_deg), 0.0
    final = False
    dt = 0.05
    for step in range(int(900 / dt)):
        dist_iaf = math.hypot(iaf_x-x, iaf_z-z)
        if not final and dist_iaf < 250:
            final = True
        if not final:
            target = math.atan2(iaf_x-x, -(iaf_z-z))
        else:
            rx, rz = x-threshold_x, z-threshold_z
            along = rx*dx + rz*dz
            cross = rx*math.cos(runway_hdg) + rz*math.sin(runway_hdg)
            corr = max(-0.32, min(0.32, -math.atan2(cross*10, max(900, -along*10))*1.15))
            target = norm(runway_hdg + corr)
        err = norm(target-heading)
        desired_roll = max(-0.42, min(0.42, err*1.25))
        roll += (desired_roll-roll)*(1-math.exp(-4.0*dt))
        heading = norm(heading + math.sin(roll)*0.78*dt)
        x += math.sin(heading)*speed*dt
        z -= math.cos(heading)*speed*dt
        rx, rz = x-threshold_x, z-threshold_z
        along = rx*dx + rz*dz
        cross = rx*math.cos(runway_hdg) + rz*math.sin(runway_hdg)
        if final and -200 <= along <= 100 and abs(cross) < 100:
            return True, step*dt, along, cross
        if abs(x)>10000 or abs(z)>10000: break
    return False, step*dt, along, cross

def main():
    cases=0; failures=[]; worst=0
    for radius in (800,1800,2600):
        for bearing in range(0,360,15):
            for heading in range(0,360,45):
                cases+=1
                ok,t,a,c=run_case(bearing,radius,heading)
                worst=max(worst,t)
                if not ok: failures.append((radius,bearing,heading,round(t,1),round(a,1),round(c,1)))
    print(f'Cases: {cases}; captured: {cases-len(failures)}; failed: {len(failures)}; max time: {worst:.1f}s')
    if failures:
        print('First failures:',failures[:20]); raise SystemExit(1)
    print('PASS: all reduced 2-D cases captured the IAF/final corridor.')
    print('LIMIT: not a full flight-physics, altitude, flare, touchdown or browser test.')
if __name__=='__main__': main()
