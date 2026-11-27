'use strict';
(function (root) {
  const G = 9.80665;
  const KNOT_TO_MS = 0.514444444444;
  const clamp = (n, lo, hi) => Math.max(lo, Math.min(hi, n));

  function windComponents(directionFromDeg, speedKts) {
    const direction = ((Number(directionFromDeg) || 0) % 360 + 360) % 360 * Math.PI / 180;
    const speedMs = Math.max(0, Number(speedKts) || 0) * KNOT_TO_MS;
    return { xMs: -Math.sin(direction) * speedMs, zMs: Math.cos(direction) * speedMs };
  }

  function groundVelocity(speedKts, headingRad, verticalSpeedMs, wind, onGround) {
    const speedMs = Math.max(0, Number(speedKts) || 0) * KNOT_TO_MS;
    const gamma = Math.atan2(Number(verticalSpeedMs) || 0, Math.max(2, speedMs));
    const forwardMs = speedMs * Math.cos(gamma);
    const windX = onGround ? 0 : (Number(wind && wind.xMs) || 0);
    const windZ = onGround ? 0 : (Number(wind && wind.zMs) || 0);
    const xMs = Math.sin(Number(headingRad) || 0) * forwardMs + windX;
    const zMs = -Math.cos(Number(headingRad) || 0) * forwardMs + windZ;
    return { xMs, zMs, groundSpeedKts: Math.hypot(xMs, zMs) / KNOT_TO_MS };
  }

  function airDensity(altitudeM) {
    const h = Math.max(0, Number(altitudeM) || 0);
    const rho0 = 1.225;
    const r = 287.05287;
    if (h <= 11000) {
      const temperatureRatio = Math.max(0.01, 1 - 0.0065 * h / 288.15);
      return rho0 * Math.pow(temperatureRatio, 4.2558797);
    }
    const t11 = 216.65;
    const rho11 = rho0 * Math.pow(1 - 0.0065 * 11000 / 288.15, 4.2558797);
    return rho11 * Math.exp(-G * (h - 11000) / (r * t11));
  }

  function calculateAero(input, spec, environment = {}) {
    const speed = Math.max(0, Number(input.speedMs) || 0);
    const verticalSpeed = Number(input.verticalSpeedMs) || 0;
    const pitch = Number(input.pitchRad) || 0;
    const roll = Number(input.rollRad) || 0;
    const altitude = Math.max(0, Number(input.altitudeM) || 0);
    const flaps = clamp(Number(input.flaps) || 0, 0, 1);
    const rho = Number.isFinite(environment.densityKgM3) && environment.densityKgM3 > 0
      ? environment.densityKgM3 : airDensity(altitude);
    const flightPathAngle = Math.atan2(verticalSpeed, Math.max(speed, 2));
    const angleOfAttack = pitch - flightPathAngle;
    const flapLift = (spec.flapLiftIncrement || 0) * flaps;
    const clLinear = spec.liftCoeffZero + spec.liftCurvePerRad * angleOfAttack + flapLift;
    const clAtStall = spec.maxLiftCoefficient + flapLift;
    let liftCoefficient = clLinear;
    if (angleOfAttack > spec.criticalAoARad) {
      liftCoefficient = clAtStall - (spec.postStallLiftDropPerRad || 2.1) * (angleOfAttack - spec.criticalAoARad);
    }
    liftCoefficient = clamp(liftCoefficient, -0.55, clAtStall);

    const dynamicPressure = 0.5 * rho * speed * speed;
    const referenceArea = spec.wingAreaM2;
    const liftN = dynamicPressure * referenceArea * liftCoefficient;
    const postStall = Math.max(0, angleOfAttack - spec.criticalAoARad);
    const dragCoefficient = spec.zeroLiftDragCoeff + spec.inducedDragFactor * liftCoefficient * liftCoefficient
      + (input.gearDown ? spec.gearDragIncrement : 0)
      + (spec.flapDragIncrement || 0) * flaps
      + (spec.postStallDragPerRad || 1.2) * postStall * postStall;
    const dragN = dynamicPressure * referenceArea * dragCoefficient;
    const powerFactor = clamp(Number(environment.powerFactor ?? 1), 0, 1.15);
    const maxSpeedMs = Math.max(1, spec.maxSpeed * KNOT_TO_MS);
    const thrustSpeedFactor = Math.max(spec.minimumThrustFactor || 0.30,
      1 - spec.thrustSpeedLoss * speed / maxSpeedMs);
    const thrustN = spec.maxThrustN * clamp(Number(input.throttle) || 0, 0, 1) * powerFactor * thrustSpeedFactor;
    const brakeN = input.onGround && input.brake ? spec.brakeForceN : 0;
    const rollingN = input.onGround ? spec.massKg * G * spec.rollingResistance : 0;
    const forwardAccelerationMs2 = input.onGround
      ? (thrustN - dragN - brakeN - rollingN) / spec.massKg
      : (thrustN - dragN) / spec.massKg - G * Math.sin(flightPathAngle);
    const verticalAccelerationMs2 = input.onGround
      ? 0 : liftN * Math.max(0.2, Math.cos(roll)) / spec.massKg - G;
    const stalled = angleOfAttack >= spec.criticalAoARad || liftCoefficient < -0.1;

    return {
      airDensityKgM3: rho,
      dynamicPressurePa: dynamicPressure,
      angleOfAttackRad: angleOfAttack,
      liftCoefficient,
      dragCoefficient,
      liftN,
      dragN,
      thrustN,
      brakeN,
      rollingResistanceN: rollingN,
      forwardAccelerationMs2,
      verticalAccelerationMs2,
      stalled
    };
  }

  function throttleForTargetSpeed(input, spec, targetSpeedMs, desiredAccelMs2 = 0, environment = {}) {
    const targetInput = { ...input, speedMs: Math.max(0, targetSpeedMs), throttle: 1, onGround: false, brake: false };
    const aero = calculateAero(targetInput, spec, environment);
    const gamma = Math.atan2(Number(input.verticalSpeedMs) || 0, Math.max(2, targetSpeedMs));
    const requiredThrustN = aero.dragN + spec.massKg * (desiredAccelMs2 + G * Math.sin(gamma));
    const throttle = clamp(requiredThrustN / Math.max(1, aero.thrustN), 0, 1);
    const commandedAero = calculateAero({ ...targetInput, throttle }, spec, environment);
    return { throttle, requiredThrustN, availableThrustN: aero.thrustN, predictedForwardAccelerationMs2: commandedAero.forwardAccelerationMs2 };
  }

  function pitchForVerticalAcceleration(input, spec, targetAccelerationMs2, environment = {}) {
    const speed = Math.max(0, Number(input.speedMs) || 0);
    const rho = Number.isFinite(environment.densityKgM3) && environment.densityKgM3 > 0
      ? environment.densityKgM3 : airDensity(input.altitudeM);
    const qS = 0.5 * rho * speed * speed * spec.wingAreaM2;
    if (qS < 1) return Number(input.pitchRad) || 0;
    const cosRoll = Math.max(0.2, Math.cos(Number(input.rollRad) || 0));
    const requiredLiftN = spec.massKg * (G + targetAccelerationMs2) / cosRoll;
    const requiredCl = requiredLiftN / qS;
    const flapLift = (spec.flapLiftIncrement || 0) * clamp(Number(input.flaps) || 0, 0, 1);
    const alpha = (requiredCl - spec.liftCoeffZero - flapLift) / spec.liftCurvePerRad;
    const gamma = Math.atan2(Number(input.verticalSpeedMs) || 0, Math.max(speed, 2));
    return gamma + alpha;
  }

  function step(input, spec, dt, environment = {}) {
    const aero = calculateAero(input, spec, environment);
    const stepSeconds = clamp(Number(dt) || 0, 0, 0.05);
    return {
      ...aero,
      speedMs: Math.max(0, Math.max(0, input.speedMs || 0) + aero.forwardAccelerationMs2 * stepSeconds),
      verticalSpeedMs: input.onGround ? 0 : (Number(input.verticalSpeedMs) || 0) + aero.verticalAccelerationMs2 * stepSeconds
    };
  }

  const api = { G, KNOT_TO_MS, airDensity, windComponents, groundVelocity, calculateAero, throttleForTargetSpeed, pitchForVerticalAcceleration, step };
  root.FlightPhysics = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : window);