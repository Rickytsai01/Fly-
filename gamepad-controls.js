'use strict';
(function (root) {
  const AXES = ['roll', 'pitch', 'yaw', 'throttle', 'brake'];
  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
  const integer = (value, fallback, min, max) => {
    const number = Number(value);
    return Number.isInteger(number) && number >= min && number <= max ? number : fallback;
  };

  function createDefaultProfile() {
    return {
      deviceIndex: -1,
      axes: { roll: 0, pitch: 1, yaw: 2, throttle: 3, brake: -1 },
      deadzone: 0.08,
      sensitivity: 1,
      invert: { roll: false, pitch: false, yaw: false, throttle: true, brake: false },
      centers: { roll: 0, pitch: 0, yaw: 0, brake: 0 },
      throttleMode: 'signed',
      brakeMode: 'signed',
      buttons: { toggleFlaps: 0, toggleGear: 1, toggleAp: 2, cycleView: 3 }
    };
  }

  function normalizeProfile(raw = {}) {
    const base = createDefaultProfile();
    const profile = raw && typeof raw === 'object' ? raw : {};
    for (const role of AXES) base.axes[role] = integer(profile.axes?.[role], base.axes[role], -1, 31);
    base.deviceIndex = integer(profile.deviceIndex, -1, -1, 15);
    base.deadzone = clamp(Number(profile.deadzone) || 0, 0, 0.35);
    base.sensitivity = clamp(Number(profile.sensitivity) || 1, 0.35, 2.5);
    for (const role of AXES) base.invert[role] = !!profile.invert?.[role];
    for (const role of ['roll', 'pitch', 'yaw', 'brake']) {
      const center = Number(profile.centers?.[role]);
      base.centers[role] = Number.isFinite(center) ? clamp(center, -0.75, 0.75) : 0;
    }
    if (profile.throttleMode === 'unipolar') base.throttleMode = 'unipolar';
    if (profile.brakeMode === 'unipolar') base.brakeMode = 'unipolar';
    for (const action of Object.keys(base.buttons)) base.buttons[action] = integer(profile.buttons?.[action], base.buttons[action], -1, 31);
    return base;
  }

  function shapeCenteredAxis(raw, profile, role) {
    const settings = normalizeProfile(profile);
    let value = clamp(Number(raw) || 0, -1, 1);
    const center = settings.centers[role] || 0;
    const offset = value - center;
    value = offset >= 0 ? offset / Math.max(0.05, 1 - center) : offset / Math.max(0.05, 1 + center);
    value = clamp(value, -1, 1);
    const magnitude = Math.abs(value);
    if (magnitude <= settings.deadzone) value = 0;
    else value = Math.sign(value) * Math.pow((magnitude - settings.deadzone) / (1 - settings.deadzone), 1 / settings.sensitivity);
    return settings.invert[role] ? -value : value;
  }

  function shapeUnipolarAxis(raw, profile, role) {
    const settings = normalizeProfile(profile);
    let value = clamp(Number(raw) || 0, 0, 1);
    if (value <= settings.deadzone) value = 0;
    else value = Math.pow((value - settings.deadzone) / (1 - settings.deadzone), 1 / settings.sensitivity);
    return settings.invert[role] ? 1 - value : value;
  }

  function readAxis(gamepad, profile, role) {
    const settings = normalizeProfile(profile);
    const index = settings.axes[role];
    if (!gamepad || index < 0 || !Array.isArray(gamepad.axes) || index >= gamepad.axes.length) return 0;
    const raw = gamepad.axes[index];
    if ((role === 'throttle' && settings.throttleMode === 'unipolar') || (role === 'brake' && settings.brakeMode === 'unipolar')) {
      return shapeUnipolarAxis(raw, settings, role);
    }
    return shapeCenteredAxis(raw, settings, role);
  }

  function readThrottle(gamepad, profile) {
    const settings = normalizeProfile(profile);
    if (settings.axes.throttle < 0) return null;
    const value = readAxis(gamepad, settings, 'throttle');
    return settings.throttleMode === 'unipolar' ? clamp(value, 0, 1) : clamp((value + 1) * 0.5, 0, 1);
  }

  function readBrake(gamepad, profile) {
    const settings = normalizeProfile(profile);
    if (settings.axes.brake < 0) return null;
    const value = readAxis(gamepad, settings, 'brake');
    return settings.brakeMode === 'unipolar' ? clamp(value, 0, 1) : clamp((value + 1) * 0.5, 0, 1);
  }

  const api = { AXES, createDefaultProfile, normalizeProfile, shapeCenteredAxis, shapeUnipolarAxis, readAxis, readThrottle, readBrake };
  root.GamepadControls = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : window);