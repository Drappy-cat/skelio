"""
Ekspor model YOLOv11-Pose PyTorch (.pt) ke format ONNX (.onnx)
untuk inferensi CPU / DirectML berlatensi rendah pada SKELIO v3.1.0.
"""

import os
import shutil
from ultralytics import YOLO

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)


def export_model(pt_path: str, out_onnx_path: str, imgsz: int = 256) -> str | None:
    if not os.path.exists(pt_path):
        print(f"⚠️ Model tidak ditemukan: {pt_path}")
        return None

    print(f"🚀 Mengekspor {pt_path} -> ONNX (imgsz={imgsz}, simplify=True)...")
    model = YOLO(pt_path)
    exported = model.export(format="onnx", imgsz=imgsz, simplify=True, dynamic=False)
    exported_str = str(exported)
    if os.path.exists(exported_str):
        os.makedirs(os.path.dirname(out_onnx_path), exist_ok=True)
        if os.path.abspath(exported_str) != os.path.abspath(out_onnx_path):
            shutil.move(exported_str, out_onnx_path)
        size_mb = os.path.getsize(out_onnx_path) / (1024 * 1024)
        print(f"✅ Berhasil: {out_onnx_path} ({size_mb:.2f} MB)")
        return out_onnx_path
    return None


if __name__ == "__main__":
    imgsz = int(os.environ.get("SKELIO_IMGSZ", "256"))
    export_model(
        os.path.join(ROOT_DIR, "models", "best_calisthenics_pose.pt"),
        os.path.join(ROOT_DIR, "models", "best_calisthenics_pose.onnx"),
        imgsz=imgsz,
    )
    nano_pt = os.path.join(ROOT_DIR, "yolo11n-pose", "weights", "best.pt")
    if os.path.exists(nano_pt):
        export_model(
            nano_pt,
            os.path.join(ROOT_DIR, "models", "best_calisthenics_nano.onnx"),
            imgsz=imgsz,
        )
