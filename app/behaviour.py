from .config import settings
from .models import BehaviourTemplate
from .schemas import BehaviourData
from .utils import average_percentage_difference, clamp


def dwell_score(stored: BehaviourTemplate, attempt: BehaviourData) -> float:
    difference = average_percentage_difference(stored.dwell_times, attempt.dwell_times)
    return clamp(100 - difference)


def flight_score(stored: BehaviourTemplate, attempt: BehaviourData) -> float:
    difference = average_percentage_difference(stored.flight_times, attempt.flight_times)
    return clamp(100 - difference)


def total_time_score(stored: BehaviourTemplate, attempt: BehaviourData) -> float:
    denominator = stored.total_time if stored.total_time != 0 else 1e-6
    difference = abs(stored.total_time - attempt.total_time) / denominator * 100
    return clamp(100 - difference)


def speed_score(stored: BehaviourTemplate, attempt: BehaviourData) -> float:
    stored_keys = len(stored.dwell_times) or 1
    attempt_keys = len(attempt.dwell_times) or 1
    stored_speed = stored_keys * 1000 / (stored.total_time or 1e-6)  # keys per second
    attempt_speed = attempt_keys * 1000 / (attempt.total_time or 1e-6)
    denominator = stored_speed if stored_speed != 0 else 1e-6
    difference = abs(stored_speed - attempt_speed) / denominator * 100
    return clamp(100 - difference)


def length_score(stored: BehaviourTemplate, attempt: BehaviourData) -> float:
    stored_len = len(stored.dwell_times)
    attempt_len = len(attempt.dwell_times)
    max_len = max(stored_len, attempt_len, 1)
    diff = abs(stored_len - attempt_len) / max_len * 100
    return clamp(100 - diff)


def error_score(stored: BehaviourTemplate, attempt: BehaviourData) -> float:
    if stored.error_count == 0 and attempt.error_count == 0:
        return 100.0
    denominator = stored.error_count if stored.error_count != 0 else 1.0
    difference = abs(stored.error_count - attempt.error_count) / denominator * 100
    return clamp(100 - difference)


def similarity_score(stored: BehaviourTemplate, attempt: BehaviourData) -> tuple[float, dict]:
    device_type = getattr(attempt, "device_type", "fine") or "fine"
    dwell_component = dwell_score(stored, attempt)
    flight_component = flight_score(stored, attempt)
    total_component = total_time_score(stored, attempt)
    speed_component = speed_score(stored, attempt)
    error_component = error_score(stored, attempt)
    length_component = length_score(stored, attempt)
    if device_type == "coarse":
        # Touch devices: reduce sensitivity to speed and duration variance.
        weights = {"dwell": 0.3, "flight": 0.3, "total": 0.12, "speed": 0.08, "length": 0.1, "error": 0.1}
    else:
        weights = {"dwell": 0.26, "flight": 0.26, "total": 0.14, "speed": 0.14, "length": 0.1, "error": 0.1}
    combined = (
        weights["dwell"] * dwell_component
        + weights["flight"] * flight_component
        + weights["total"] * total_component
        + weights["speed"] * speed_component
        + weights["length"] * length_component
        + weights["error"] * error_component
    )
    score = round(clamp(combined), 2)
    components = {
        "dwell": round(dwell_component, 2),
        "flight": round(flight_component, 2),
        "total_time": round(total_component, 2),
        "speed": round(speed_component, 2),
        "length": round(length_component, 2),
        "errors": round(error_component, 2),
    }
    return score, components


def is_behaviour_match(stored: BehaviourTemplate, attempt: BehaviourData) -> tuple[bool, float, list[str]]:
    reasons: list[str] = []
    if abs(len(stored.dwell_times) - len(attempt.dwell_times)) > 1:
        # Strong guard: materially different key counts should not match.
        reasons.append(
            f"Key count differs: expected ~{len(stored.dwell_times)}, got {len(attempt.dwell_times)}"
        )
        return False, 0.0, reasons

    # Early reject if overall tempo is far off (large speed/total time drift).
    stored_keys = len(stored.dwell_times) or 1
    attempt_keys = len(attempt.dwell_times) or 1
    stored_speed = stored_keys * 1000 / (stored.total_time or 1e-6)
    attempt_speed = attempt_keys * 1000 / (attempt.total_time or 1e-6)
    speed_ratio = attempt_speed / (stored_speed or 1e-6)
    total_ratio = (attempt.total_time or 1e-6) / (stored.total_time or 1e-6)
    if speed_ratio < 0.6 or speed_ratio > 1.6 or total_ratio < 0.6 or total_ratio > 1.6:
        reasons.append("Overall tempo differs too much from enrollment")
        return False, 0.0, reasons

    score, components = similarity_score(stored, attempt)
    if score >= settings.behaviour_threshold:
        return True, score, reasons

    if components["dwell"] < settings.behaviour_threshold:
        reasons.append(f"Dwell timings differ (score {components['dwell']}%)")
    if components["flight"] < settings.behaviour_threshold:
        reasons.append(f"Flight timings differ (score {components['flight']}%)")
    if components["speed"] < settings.behaviour_threshold:
        reasons.append(f"Typing speed differs (score {components['speed']}%)")
    if components["total_time"] < settings.behaviour_threshold:
        reasons.append(f"Total duration differs (score {components['total_time']}%)")
    if components["length"] < settings.behaviour_threshold:
        reasons.append(f"Key count alignment off (score {components['length']}%)")
    if components["errors"] < settings.behaviour_threshold and attempt.error_count:
        reasons.append(f"Too many corrections (score {components['errors']}%)")
    if not reasons:
        reasons.append("Behavioural score below threshold")

    return False, score, reasons
