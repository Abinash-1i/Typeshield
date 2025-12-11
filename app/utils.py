from typing import List, Tuple


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def align_vectors(reference: List[float], sample: List[float]) -> Tuple[List[float], List[float]]:
    """
    Align vectors to the same length by trimming to the shortest length.
    Returns trimmed copies to avoid mutating inputs.
    """
    if not reference or not sample:
        return reference, sample
    length = min(len(reference), len(sample))
    return reference[:length], sample[:length]


def average_percentage_difference(reference: List[float], sample: List[float]) -> float:
    """
    Computes the average percentage difference between two vectors.
    Percentage difference is |a-b| / (a + 1e-6) * 100 to avoid division by zero.
    Length mismatches are penalized by treating extra/missing items as a 100% difference.
    """
    if not reference or not sample:
        return 100.0
    ref_len, sample_len = len(reference), len(sample)
    min_len = min(ref_len, sample_len)
    max_len = max(ref_len, sample_len)

    diffs = []
    for ref_val, sample_val in zip(reference[:min_len], sample[:min_len]):
        denominator = ref_val if ref_val != 0 else 1e-6
        diffs.append(abs(ref_val - sample_val) / denominator * 100)

    unmatched = max_len - min_len
    if unmatched:
        diffs.extend([100.0] * unmatched)

    return sum(diffs) / max_len if max_len else 100.0
