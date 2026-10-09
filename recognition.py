"""Prediction smoothing and word formation for SignBridge."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import time

def preprocess_frame(frame_bgr: "np.ndarray", size: tuple[int, int]) -> "np.ndarray":
    """Crop a centered square, normalize it, and create a model batch."""
    import cv2
    import numpy as np

    if frame_bgr is None or frame_bgr.size == 0:
        raise ValueError("Empty camera frame")

    height, width = frame_bgr.shape[:2]
    side = int(min(height, width) * 0.82)
    x0 = max((width - side) // 2, 0)
    y0 = max((height - side) // 2, 0)
    hand_roi = frame_bgr[y0 : y0 + side, x0 : x0 + side]
    resized = cv2.resize(hand_roi, size, interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    three_channel = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    return np.expand_dims(three_channel.astype(np.float32) / 255.0, axis=0)


@dataclass
class PredictionSmoother:
    window_size: int = 7
    _history: deque = field(init=False)

    def __post_init__(self) -> None:
        self._history = deque(maxlen=self.window_size)

    def reset(self) -> None:
        self._history.clear()

    def update(self, probabilities: "np.ndarray") -> tuple[int, float, float]:
        import numpy as np

        values = np.asarray(probabilities, dtype=np.float32).reshape(-1)
        self._history.append(values)
        averaged = np.mean(self._history, axis=0)
        order = np.argsort(averaged)
        best_index = int(order[-1])
        best = float(averaged[best_index])
        second = float(averaged[order[-2]]) if len(order) > 1 else 0.0
        return best_index, best, best - second


@dataclass
class WordFormer:
    confidence_threshold: float = 0.72
    margin_threshold: float = 0.12
    stability_seconds: float = 0.85
    release_seconds: float = 0.35
    space_seconds: float = 1.8
    sentence: str = ""
    candidate: str = ""
    candidate_since: float | None = None
    last_hand_time: float = field(default_factory=time.monotonic)
    accepted_letter: str = ""
    released_since: float | None = None
    space_added: bool = False

    def clear(self) -> None:
        self.sentence = ""
        self.reset_tracking()

    def backspace(self) -> str:
        self.sentence = self.sentence[:-1]
        return self.sentence

    def reset_tracking(self) -> None:
        self.candidate = ""
        self.candidate_since = None
        self.accepted_letter = ""
        self.released_since = None
        self.space_added = False
        self.last_hand_time = time.monotonic()

    def update(
        self,
        letter: str,
        confidence: float,
        margin: float,
        hand_present: bool,
        now: float | None = None,
    ) -> dict:
        now = time.monotonic() if now is None else now
        is_valid = (
            hand_present
            and bool(letter)
            and confidence >= self.confidence_threshold
            and margin >= self.margin_threshold
        )

        if not hand_present:
            if self.released_since is None:
                self.released_since = now
            if now - self.released_since >= self.release_seconds:
                self.accepted_letter = ""
            if (
                self.sentence
                and not self.sentence.endswith(" ")
                and not self.space_added
                and now - self.last_hand_time >= self.space_seconds
            ):
                self.sentence += " "
                self.space_added = True
            self.candidate = ""
            self.candidate_since = None
        elif is_valid:
            self.last_hand_time = now
            self.released_since = None
            self.space_added = False
            if letter != self.candidate:
                self.candidate = letter
                self.candidate_since = now
            elif (
                self.candidate_since is not None
                and now - self.candidate_since >= self.stability_seconds
                and letter != self.accepted_letter
            ):
                self.sentence += letter
                self.accepted_letter = letter
                self.candidate_since = now
        else:
            self.candidate = ""
            self.candidate_since = None

        progress = 0.0
        if is_valid and self.candidate_since is not None and letter != self.accepted_letter:
            progress = min((now - self.candidate_since) / self.stability_seconds, 1.0)

        return {
            "pred_letter": letter if is_valid else "",
            "confidence": round(confidence * 100, 1) if hand_present else 0.0,
            "confidence_margin": round(margin * 100, 1) if hand_present else 0.0,
            "current_sentence": self.sentence,
            "progress": round(progress, 3),
            "hand_present": hand_present,
        }
