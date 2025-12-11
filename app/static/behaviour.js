document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("form");
    const passwordInput = document.getElementById("password");
    const behaviourField = document.getElementById("behaviour_data");
    const statKeys = document.getElementById("stat-keys");
    const statErrors = document.getElementById("stat-errors");
    const statDuration = document.getElementById("stat-duration");
    const statSpeed = document.getElementById("stat-speed");
    const barSpeed = document.getElementById("bar-speed");
    const barDuration = document.getElementById("bar-duration");
    const barSpeedLabel = document.getElementById("bar-speed-label");
    const barDurationLabel = document.getElementById("bar-duration-label");

    if (!form || !passwordInput || !behaviourField) return;

    const useCoarseCapture = window.matchMedia && window.matchMedia("(pointer: coarse)").matches;
    const deviceType = useCoarseCapture ? "coarse" : "fine";
    const dwellTimes = [];
    const flightTimes = [];
    const keyUpTimes = [];
    let lastKeyUp = null;
    let lastInputTime = null;
    let lastLength = 0;
    let startTime = null;
    let errorCount = 0;
    let pendingDown = null;

    const updateStats = () => {
        if (statKeys) statKeys.textContent = dwellTimes.length.toString();
        if (statErrors) statErrors.textContent = errorCount.toString();
        const durationMs = startTime !== null && lastKeyUp !== null ? Math.max(0, Math.round(lastKeyUp - startTime)) : 0;
        if (statDuration) statDuration.textContent = `${durationMs} ms`;
        const speed = durationMs > 0 ? (dwellTimes.length * 1000) / durationMs : 0;
        if (statSpeed) statSpeed.textContent = `${speed.toFixed(1)} k/s`;

        // Normalize for progress bars: assume typical speed up to 8 k/s; duration 0-5000ms window.
        const speedPercent = Math.max(0, Math.min(100, (speed / 8) * 100));
        const durationPercent = Math.max(0, Math.min(100, (durationMs / 5000) * 100));
        if (barSpeed) barSpeed.style.width = `${speedPercent.toFixed(0)}%`;
        if (barDuration) barDuration.style.width = `${durationPercent.toFixed(0)}%`;
        if (barSpeedLabel) barSpeedLabel.textContent = `${speedPercent.toFixed(0)}%`;
        if (barDurationLabel) barDurationLabel.textContent = `${durationPercent.toFixed(0)}%`;
    };

    passwordInput.addEventListener("keydown", (event) => {
        if (useCoarseCapture) return; // fallback to input-based capture on touch devices
        const now = performance.now();

        if (event.key === "Backspace") {
            errorCount += 1;
            // Remove the last recorded keystroke so timing vectors match the final password.
            if (dwellTimes.length) dwellTimes.pop();
            if (keyUpTimes.length) keyUpTimes.pop();
            if (flightTimes.length) flightTimes.pop();
            lastKeyUp = keyUpTimes.length ? keyUpTimes[keyUpTimes.length - 1] : null;
            if (!keyUpTimes.length) startTime = null;
            pendingDown = null;
            updateStats();
            return;
        }

        if (startTime === null) startTime = now;

        // flight time is gap between previous keyup and this keydown
        if (lastKeyUp !== null) {
            flightTimes.push(now - lastKeyUp);
        }
        pendingDown = now;
    });

    passwordInput.addEventListener("keyup", (event) => {
        if (useCoarseCapture) return;
        const now = performance.now();
        if (pendingDown !== null) {
            const dwell = now - pendingDown;
            dwellTimes.push(dwell);
            keyUpTimes.push(now);
            pendingDown = null;
        }
        lastKeyUp = now;
        updateStats();
    });

    // Fallback capture for mobile/touch keyboards where keydown/keyup are inconsistent
    passwordInput.addEventListener("input", () => {
        if (!useCoarseCapture) return;
        const now = performance.now();
        const currentLength = passwordInput.value.length;
        const diff = currentLength - lastLength;

        if (diff === 1) {
            if (startTime === null) startTime = now;
            if (lastInputTime !== null) {
                const delta = now - lastInputTime;
                flightTimes.push(delta);
                dwellTimes.push(Math.min(300, Math.max(60, delta)));
            } else {
                dwellTimes.push(120);
            }
            lastKeyUp = now;
            lastInputTime = now;
        } else if (diff < 0) {
            const remove = Math.min(dwellTimes.length, Math.abs(diff));
            if (remove > 0) {
                dwellTimes.splice(-remove);
                flightTimes.splice(-remove);
                keyUpTimes.splice(-remove);
            }
            errorCount += Math.abs(diff);
            lastKeyUp = dwellTimes.length ? lastKeyUp : null;
            lastInputTime = now;
            if (!dwellTimes.length) startTime = null;
        } else if (diff > 1) {
            // multiple characters injected (autocomplete/paste) — discard capture to avoid bad data
            dwellTimes.length = 0;
            flightTimes.length = 0;
            keyUpTimes.length = 0;
            errorCount = 0;
            startTime = null;
            lastKeyUp = null;
            lastInputTime = null;
        }

        lastLength = currentLength;
        updateStats();
    });

    form.addEventListener("submit", (event) => {
        if (startTime === null || lastKeyUp === null) {
            event.preventDefault();
            alert("Type your password to capture behaviour data.");
            return;
        }

        const payload = {
            dwell_times: dwellTimes,
            flight_times: flightTimes,
            total_time: lastKeyUp - startTime,
            error_count: errorCount,
            device_type: deviceType,
        };

        behaviourField.value = JSON.stringify(payload);
    });

    updateStats();
});
