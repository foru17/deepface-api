"""Vision inference (RetinaFace + DeepFace) and image annotation helpers."""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np
from starlette.concurrency import run_in_threadpool

OUTER_COLOR = (255, 255, 255)
INNER_COLOR = (0, 165, 255)
OUTER_THICKNESS = 6
INNER_THICKNESS = 3


def draw_detections_with_info(img: np.ndarray, faces: list[dict[str, Any]]) -> np.ndarray:
    """Render bounding boxes and a small info badge per face."""

    img_result = img.copy()

    for face in faces:
        area = face["facial_area"]
        x, y, w, h = area["x"], area["y"], area["w"], area["h"]

        cv2.rectangle(img_result, (x, y), (x + w, y + h), OUTER_COLOR, OUTER_THICKNESS)
        cv2.rectangle(img_result, (x, y), (x + w, y + h), INNER_COLOR, INNER_THICKNESS)

        info_lines: list[str] = []
        if face.get("score") is not None:
            info_lines.append(f"Conf: {face['score']:.2f}")
        if face.get("age") is not None:
            info_lines.append(f"Age: {face['age']}")
        if face.get("gender"):
            info_lines.append(f"Gender: {face['gender']}")
        if face.get("dominant_emotion"):
            info_lines.append(f"Emotion: {face['dominant_emotion']}")

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        text_thickness = 2
        line_height = 25
        padding = 5

        total_height = len(info_lines) * line_height
        start_y = max(total_height + padding, y)

        for i, line in enumerate(info_lines):
            (text_width, text_height), _ = cv2.getTextSize(line, font, font_scale, text_thickness)
            text_y = start_y - (i * line_height)
            text_x = min(x, img_result.shape[1] - text_width - padding)

            cv2.rectangle(
                img_result,
                (text_x - padding, text_y - text_height - padding),
                (text_x + text_width + padding, text_y + padding),
                OUTER_COLOR,
                -1,
            )
            cv2.rectangle(
                img_result,
                (text_x - padding + 2, text_y - text_height - padding + 2),
                (text_x + text_width + padding - 2, text_y + padding - 2),
                INNER_COLOR,
                -1,
            )
            cv2.putText(
                img_result,
                line,
                (text_x, text_y),
                font,
                font_scale,
                (255, 255, 255),
                text_thickness,
            )

    return img_result


def ensure_face_area_within_bounds(
    area: dict[str, int], img_shape: tuple[int, ...]
) -> dict[str, int]:
    height, width = img_shape[:2]
    x = max(0, min(area["x"], width - 1))
    y = max(0, min(area["y"], height - 1))
    w = max(1, min(area["w"], width - x))
    h = max(1, min(area["h"], height - y))
    return {"x": x, "y": y, "w": w, "h": h}


async def detect_faces(img: np.ndarray) -> list[dict[str, Any]]:
    """Detect faces with RetinaFace. Heavy import deferred to first call."""

    from retinaface import RetinaFace  # type: ignore[import-not-found]

    faces = await run_in_threadpool(RetinaFace.detect_faces, img)
    if not isinstance(faces, dict):
        return []

    normalized_faces: list[dict[str, Any]] = []
    for face_data in faces.values():
        area = {
            "x": int(face_data["facial_area"][0]),
            "y": int(face_data["facial_area"][1]),
            "w": int(face_data["facial_area"][2] - face_data["facial_area"][0]),
            "h": int(face_data["facial_area"][3] - face_data["facial_area"][1]),
        }
        normalized_faces.append(
            {
                "position": ensure_face_area_within_bounds(area, img.shape),
                "confidence": (float(face_data["score"]) if "score" in face_data else None),
            }
        )

    return normalized_faces


async def analyze_single_face(
    img: np.ndarray,
    area: dict[str, int],
    include_race: bool,
    lightweight: bool = False,
) -> dict[str, Any]:
    """Run DeepFace attribute analysis on a single face crop."""

    from deepface import DeepFace  # type: ignore[import-not-found]

    face_img = img[area["y"] : area["y"] + area["h"], area["x"] : area["x"] + area["w"]]

    actions = ["age", "gender", "emotion"]
    if include_race and not lightweight:
        actions.append("race")

    analysis = await run_in_threadpool(DeepFace.analyze, face_img, actions, False)
    if isinstance(analysis, list):
        analysis = analysis[0]

    gender = "Woman" if analysis["gender"]["Woman"] > 50 else "Man"
    result: dict[str, Any] = {
        "age": int(analysis["age"]),
        "gender": gender,
        "dominant_emotion": str(analysis["dominant_emotion"]),
    }

    if not lightweight:
        result["emotion"] = {k: float(v) for k, v in analysis["emotion"].items()}

    if include_race and not lightweight:
        result["dominant_race"] = str(analysis["dominant_race"])
        result["race"] = {k: float(v) for k, v in analysis["race"].items()}

    return result
