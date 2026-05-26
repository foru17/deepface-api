"""Face detection and analysis endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import cv2
from fastapi import APIRouter, Depends, File, Query, Response, UploadFile

from ...config import Settings, get_settings
from ...logging import logger
from ...schemas import AnalyzeResponse, ErrorResponse
from ...services import (
    analyze_single_face,
    detect_faces,
    draw_detections_with_info,
    read_and_decode_upload,
)

router = APIRouter()


_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ErrorResponse, "description": "Invalid upload"},
    413: {"model": ErrorResponse, "description": "Payload too large"},
    500: {"model": ErrorResponse, "description": "Internal server error"},
}


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Detect faces and (optionally) analyze attributes",
    responses=_ERROR_RESPONSES,
)
async def analyze(
    file: UploadFile = File(..., description="Image file (jpg/png/webp/...)."),
    save_render: bool = Query(
        default=False,
        description="If true, save annotated image to OUTPUT_DIR and return its path.",
    ),
    include_race: bool = Query(
        default=True,
        description="Include race-related attributes in the response.",
    ),
    settings: Settings = Depends(get_settings),
) -> AnalyzeResponse:
    img, _ = await read_and_decode_upload(file, settings.max_upload_size_mb)
    detected_faces = await detect_faces(img)

    faces: list[dict[str, Any]] = []
    for detected_face in detected_faces:
        face_info: dict[str, Any] = {
            "position": detected_face["position"],
            "confidence": detected_face["confidence"],
        }
        try:
            analysis = await analyze_single_face(
                img, detected_face["position"], include_race=include_race
            )
            face_info.update(analysis)
        except Exception as exc:
            logger.warning("face analysis failed: %s", exc)
        faces.append(face_info)

    output_path: str | None = None
    if save_render:
        draw_payload = [
            {
                "facial_area": face["position"],
                "score": face["confidence"],
                "age": face.get("age"),
                "gender": face.get("gender"),
                "dominant_emotion": face.get("dominant_emotion"),
            }
            for face in faces
        ]
        img_result = draw_detections_with_info(img, draw_payload)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_path = str(settings.output_dir / f"result_{timestamp}.jpg")
        cv2.imwrite(output_path, img_result)

    return AnalyzeResponse(
        status="success",
        faces_detected=len(faces),
        faces=faces,  # pydantic will coerce dicts → FaceAnalysis
        output_file=output_path,
    )


@router.post(
    "/detect_and_return",
    summary="Return annotated JPEG with detection overlays",
    responses={
        **_ERROR_RESPONSES,
        200: {
            "content": {"image/jpeg": {}},
            "description": "Annotated JPEG image",
        },
    },
)
async def detect_and_return(
    file: UploadFile = File(..., description="Image file."),
    info_display: bool = Query(default=False, description="Overlay age / gender / emotion text."),
    settings: Settings = Depends(get_settings),
) -> Response:
    img, _ = await read_and_decode_upload(file, settings.max_upload_size_mb)
    detected_faces = await detect_faces(img)

    face_list: list[dict[str, Any]] = []
    for detected_face in detected_faces:
        face_info: dict[str, Any] = {
            "facial_area": detected_face["position"],
            "score": detected_face["confidence"],
        }
        if info_display:
            try:
                analysis = await analyze_single_face(
                    img,
                    detected_face["position"],
                    include_race=False,
                    lightweight=True,
                )
                face_info.update(analysis)
            except Exception as exc:
                logger.warning("face analysis failed in detect_and_return: %s", exc)
        face_list.append(face_info)

    img_result = draw_detections_with_info(img, face_list)
    _, img_encoded = cv2.imencode(".jpg", img_result)

    return Response(
        content=img_encoded.tobytes(),
        media_type="image/jpeg",
        headers={
            "X-Faces-Detected": str(len(face_list)),
            "X-Detection-Status": "success" if face_list else "no_face",
        },
    )
