"""
SKELIO Low-Latency Split Pipeline API (FastAPI + Binary WebSocket).
Menjalankan inferensi YOLOv11-Pose & ByteTrack di server eksternal,
lalu mengirim balik hanya koordinat keypoint ternormalisasi & telemetri
ringan (~400 bytes) ke aplikasi mobile Android (Bare React Native).
"""

import asyncio
import base64
import json
import os
import sys
import threading
import time
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.biomechanical_pipeline import BiomechanicalPipeline

VALID_MODES = {"PUSH-UP", "SQUAT", "SIT-UP", "AUTO"}
DEFAULT_IMGSZ = int(os.environ.get("SKELIO_IMGSZ", "320"))

app = FastAPI(
    title="SKELIO Split-Pipeline API",
    version="3.0.0",
    description="Low-latency pose telemetry WebSocket backend for SKELIO Native Android",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_pipeline_lock = threading.Lock()
_pipeline: Optional[BiomechanicalPipeline] = None
_session_active = False
_session_start_time = time.time()
_session_duration_seconds = 0
_workout_history: List[Dict[str, Any]] = []
_last_rep_recorded: Dict[int, int] = {}


class ModeRequest(BaseModel):
    mode: str


def get_pipeline() -> BiomechanicalPipeline:
    """Menginisialisasi dan mengembalikan instance tunggal BiomechanicalPipeline."""
    global _pipeline
    if _pipeline is None:
        model_path = os.path.join(ROOT_DIR, "models", "best_calisthenics_pose.pt")
        if not os.path.exists(model_path):
            model_path = os.path.join(ROOT_DIR, "yolo11n-pose.pt")
        _pipeline = BiomechanicalPipeline(pose_model_path=model_path, imgsz=DEFAULT_IMGSZ)
    return _pipeline


def _record_completed_reps(pipe: BiomechanicalPipeline) -> None:
    now_iso = time.strftime("%H:%M:%S")
    for tid, pstate in pipe.persons.items():
        prev_reps = _last_rep_recorded.get(tid, 0)
        if pstate.rep_count > prev_reps:
            is_clean = pstate.clean_reps > 0 and not pstate.current_rep_fault
            status_text = getattr(pstate, "status", "BERLATIH")
            _workout_history.append({
                "id": len(_workout_history) + 1,
                "time": now_iso,
                "track_id": tid,
                "exercise": pstate.exercise_mode,
                "rep_number": pstate.rep_count,
                "depth_pct": round(float(pstate.depth_pct), 1),
                "angle_deg": round(float(getattr(pstate, "primary_angle", 0.0)), 1),
                "posture_angle": round(float(getattr(pstate, "posture_angle", 0.0)), 1),
                "status": "Bersih (Clean)" if is_clean else status_text,
                "is_clean": is_clean,
                "raw_fault": None if is_clean else status_text,
            })
            _last_rep_recorded[tid] = pstate.rep_count


def _infer_jpeg_bytes(jpeg_bytes: bytes) -> Dict[str, Any]:
    """Decode frame JPEG ringan dan jalankan pipeline tanpa menggambar HUD OpenCV."""
    arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        return {"error": "invalid_jpeg", "persons": []}

    t0 = time.perf_counter()
    with _pipeline_lock:
        pipe = get_pipeline()
        telemetry = pipe.process_frame_telemetry(frame)
        _record_completed_reps(pipe)
    infer_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    telemetry["infer_ms"] = infer_ms
    telemetry["type"] = "telemetry"
    return telemetry


@app.on_event("startup")
def warmup_pipeline() -> None:
    """Preload model saat server start agar koneksi WebSocket pertama tidak terkena cold-start."""
    with _pipeline_lock:
        pipe = get_pipeline()
        dummy = np.zeros((320, 320, 3), dtype=np.uint8)
        pipe.process_frame_telemetry(dummy)


@app.get("/api/health")
def health() -> Dict[str, Any]:
    with _pipeline_lock:
        pipe = get_pipeline()
        return {
            "status": "online",
            "version": "3.0.0",
            "device": str(pipe.device),
            "imgsz": pipe.imgsz,
            "active_mode": pipe.active_mode,
            "fps": round(pipe.fps, 1),
        }


@app.post("/api/set_mode")
def set_mode(req: ModeRequest) -> Dict[str, Any]:
    mode = req.mode.strip().upper()
    if mode not in VALID_MODES:
        raise HTTPException(status_code=400, detail=f"Mode tidak valid: {mode}")
    with _pipeline_lock:
        pipe = get_pipeline()
        pipe.active_mode = mode
    return {"success": True, "active_mode": mode}


@app.post("/api/reset_reps")
def reset_reps() -> Dict[str, Any]:
    with _pipeline_lock:
        pipe = get_pipeline()
        pipe.reset_all_reps()
        _last_rep_recorded.clear()
        _workout_history.clear()
    return {"success": True, "message": "Repetisi berhasil di-reset"}


@app.post("/api/session_start")
def session_start() -> Dict[str, Any]:
    global _session_active, _session_start_time
    with _pipeline_lock:
        pipe = get_pipeline()
        pipe.reset_all_reps()
        _last_rep_recorded.clear()
        _workout_history.clear()
        _session_active = True
        _session_start_time = time.time()
    return {"success": True}


@app.post("/api/session_stop")
def session_stop() -> Dict[str, Any]:
    global _session_active, _session_duration_seconds
    if _session_active:
        _session_duration_seconds = int(time.time() - _session_start_time)
        _session_active = False
    return {"success": True, "duration": _session_duration_seconds}


@app.get("/api/session_summary")
def session_summary() -> Dict[str, Any]:
    with _pipeline_lock:
        pipe = get_pipeline()
        total_reps = 0
        clean_reps = 0
        if pipe.persons:
            primary = max(pipe.persons.values(), key=lambda p: p.rep_count)
            total_reps = primary.rep_count
            clean_reps = primary.clean_reps
        elif _workout_history:
            total_reps = len(_workout_history)
            clean_reps = sum(1 for r in _workout_history if r.get("is_clean"))

        depths = [r["depth_pct"] for r in _workout_history if "depth_pct" in r]
        avg_depth = round(sum(depths) / max(1, len(depths)), 1) if depths else 0.0
        dur_sec = int(time.time() - _session_start_time) if _session_active else _session_duration_seconds
        calories = round(max(0.1, dur_sec / 60.0) * 7.2, 1)

        if total_reps == 0:
            score = 0
            grade = "N/A"
        else:
            depth_score = min(35.0, (avg_depth / 70.0) * 35.0)
            clean_score = (clean_reps / total_reps) * 65.0
            score = min(100, max(0, round(clean_score + depth_score)))
            grade = "A" if score >= 90 else ("B" if score >= 80 else ("C" if score >= 70 else "D"))

        return {
            "exercise": pipe.active_mode,
            "total_reps": total_reps,
            "clean_reps": clean_reps,
            "bad_reps": max(0, total_reps - clean_reps),
            "accuracy_pct": round((clean_reps / max(1, total_reps)) * 100, 1),
            "avg_depth": avg_depth,
            "duration_seconds": dur_sec,
            "calories_burned": calories,
            "score": score,
            "grade": grade,
            "history": _workout_history[-30:][::-1],
        }


@app.websocket("/ws/pose")
async def ws_pose(websocket: WebSocket) -> None:
    """
    Endpoint Binary/JSON WebSocket untuk klien native Android.
    Menerima:
      - bytes: frame JPEG (opsional diawali header 8-byte timestamp uint64 little-endian atau JPEG langsung)
      - text JSON: kontrol ('set_mode', 'reset', 'ping') atau {'type': 'frame', 'jpeg_b64': ..., 'ts': ...}
    """
    await websocket.accept()
    with _pipeline_lock:
        pipe = get_pipeline()
        initial_mode = pipe.active_mode

    await websocket.send_text(json.dumps({
        "type": "connected",
        "active_mode": initial_mode,
        "imgsz": DEFAULT_IMGSZ,
    }))

    try:
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                break

            raw_bytes = message.get("bytes")
            text_data = message.get("text")
            client_ts = None

            if raw_bytes is not None:
                # Dukung JPEG mentah (FF D8 ...) atau [8-byte timestamp ms] + JPEG
                if len(raw_bytes) > 10 and raw_bytes[0:2] != b"\xff\xd8" and raw_bytes[8:10] == b"\xff\xd8":
                    client_ts = int.from_bytes(raw_bytes[:8], "little")
                    raw_bytes = raw_bytes[8:]
                result = await asyncio.to_thread(_infer_jpeg_bytes, raw_bytes)
                if client_ts is not None:
                    result["ts"] = client_ts
                await websocket.send_text(json.dumps(result, separators=(",", ":")))
                continue

            if text_data is not None:
                try:
                    payload = json.loads(text_data)
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({"type": "error", "message": "invalid_json"}))
                    continue

                msg_type = payload.get("type", "")
                if msg_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong", "ts": payload.get("ts")}))
                elif msg_type == "set_mode":
                    mode = str(payload.get("mode", "PUSH-UP")).upper()
                    if mode in VALID_MODES:
                        with _pipeline_lock:
                            get_pipeline().active_mode = mode
                        await websocket.send_text(json.dumps({"type": "mode_updated", "active_mode": mode}))
                elif msg_type == "reset":
                    with _pipeline_lock:
                        get_pipeline().reset_all_reps()
                        _last_rep_recorded.clear()
                        _workout_history.clear()
                    await websocket.send_text(json.dumps({"type": "reset_done"}))
                elif msg_type == "frame" and payload.get("jpeg_b64"):
                    b64_str = payload["jpeg_b64"]
                    if "," in b64_str:
                        b64_str = b64_str.split(",", 1)[1]
                    jpg = base64.b64decode(b64_str)
                    result = await asyncio.to_thread(_infer_jpeg_bytes, jpg)
                    if "ts" in payload:
                        result["ts"] = payload["ts"]
                    await websocket.send_text(json.dumps(result, separators=(",", ":")))
    except WebSocketDisconnect:
        pass
