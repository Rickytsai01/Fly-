'use strict';
const assert = require('node:assert/strict');
const fp = require('../flight-physics.js');
const c172 = { massKg: 1090, wingAreaM2: 16.2, liftCoeffZero: 0.22, liftCurvePerRad: 6.0, criticalAoARad: 0.255, maxLiftCoefficient: 1.75, postStallLiftDropPerRad: 2.1, zeroLiftDragCoeff: 0.027, inducedDragFactor: 0.045, gearDragIncrement: 0.012, flapLiftIncrement: 0.55, flapDragIncrement: 0.018, postStallDragPerRad: 1.2, maxThrustN: 2850, thrustSpeedLoss: 0.42, minimumThrustFactor: 0.3, maxSpeed: 163, brakeForceN: 8500, rollingResistance: 0.018 };
const boeing = { ...c172, massKg: 58000, wingAreaM2: 124.6, criticalAoARad: 0.24, maxLiftCoefficient: 2.13, zeroLiftDragCoeff: 0.022, inducedDragFactor: 0.045, gearDragIncrement: 0.012, flapLiftIncrement: 0.75, flapDragIncrement: 0.025, maxThrustN: 205000, thrustSpeedLoss: 0.67, maxSpeed: 365, brakeForceN: 125000, rollingResistance: 0.016 };
const airborne = { speedMs: 55 * fp.KNOT_TO_MS, verticalSpeedMs: 0, pitchRad: 0.20, rollRad: 0, altitudeM: 0, throttle: 0.9, onGround: false, brake: false, gearDown: true, flaps: 0 };
const lift = fp.calculateAero(airborne, c172);
assert.ok(lift.liftN > 0 && lift.dragN > 0 && lift.thrustN > 0);
assert.ok(fp.airDensity(3000) < fp.airDensity(0));
assert.ok(fp.calculateAero({ ...airborne, altitudeM: 5000 }, c172).liftN < lift.liftN);
assert.ok(fp.calculateAero({ ...airborne, flaps: 1 }, c172).liftN > lift.liftN);
assert.ok(fp.calculateAero({ ...airborne, gearDown: true }, c172).dragN > fp.calculateAero({ ...airborne, gearDown: false }, c172).dragN);
const parked = { ...airborne, speedMs: 30, onGround: true, brake: false, throttle: 0.4, pitchRad: 0 };
const rolling = fp.step(parked, c172, 1 / 120);
const braking = fp.step({ ...parked, brake: true }, c172, 1 / 120);
assert.ok(rolling.speedMs > parked.speedMs);
assert.ok(braking.speedMs < rolling.speedMs);
const stall = fp.calculateAero({ ...airborne, pitchRad: 0.6 }, c172);
assert.equal(stall.stalled, true);
const targetPitch = fp.pitchForVerticalAcceleration({ ...airborne, speedMs: 70, altitudeM: 0 }, c172, 0);
const target = fp.calculateAero({ ...airborne, speedMs: 70, pitchRad: targetPitch }, c172);
assert.ok(Math.abs(target.verticalAccelerationMs2) < 0.15);
const cruiseCase = { speedMs: 122 * fp.KNOT_TO_MS, verticalSpeedMs: 0, pitchRad: 0, rollRad: 0, altitudeM: 1200, throttle: 0.5, onGround: false, gearDown: false, flaps: 0 };
const cruisePitch = fp.pitchForVerticalAcceleration(cruiseCase, c172, 0);
const holdInput = { ...cruiseCase, pitchRad: cruisePitch };
const hold = fp.throttleForTargetSpeed(holdInput, c172, holdInput.speedMs, 0, { powerFactor: 0.96 });
assert.ok(hold.throttle > 0 && hold.throttle < 1);
assert.ok(Math.abs(hold.predictedForwardAccelerationMs2) < 1e-8);
for (const [spec, rotationPitch, vr] of [[c172, 0.19, 55], [boeing, 0.24, 130]]) {
  let speedMs = 0, verticalSpeedMs = 0, altitudeM = 0, onGround = true, time = 0;
  for (; time < 90 && altitudeM < 30; time += 1 / 120) {
    const pitchRad = speedMs / fp.KNOT_TO_MS >= vr ? rotationPitch : 0;
    const input = { speedMs, verticalSpeedMs, pitchRad, rollRad: 0, altitudeM, throttle: 0.9, onGround, brake: false, gearDown: true, flaps: 0.75 };
    const result = fp.step(input, spec, 1 / 120);
    speedMs = result.speedMs;
    if (onGround && speedMs / fp.KNOT_TO_MS >= vr && result.liftN >= spec.massKg * fp.G * 0.94) onGround = false;
    else if (!onGround) { verticalSpeedMs = result.verticalSpeedMs; altitudeM += verticalSpeedMs / 120; }
  }
  assert.ok(!onGround && altitudeM >= 30, 'takeoff should climb above 30 m');
}
for (const spec of [c172, boeing]) {
  const result = fp.step({ ...airborne, speedMs: 100, pitchRad: 0.04, altitudeM: 6000 }, spec, 1 / 120);
  for (const value of Object.values(result)) if (typeof value === 'number') assert.ok(Number.isFinite(value));
}
console.log('PASS flight physics: SI forces, density, flaps, gear, braking, stall, AP trim and finite integration');