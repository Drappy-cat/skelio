import os
import glob
import cv2
import re
from biomechanical_pipeline import BiomechanicalPipeline

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def build_demo_video(exercise_type="Push-up", mode="PUSH-UP", fps=15):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    train_dir = os.path.join(base_dir, "dataset", "exercise.v4-up-exercise.yolov8", "train", "images")
    output_dir = os.path.join(base_dir, "assets_sempro")
    os.makedirs(output_dir, exist_ok=True)
    
    # Ambil frame yang relevan
    pattern = os.path.join(train_dir, f"{exercise_type}*")
    image_paths = sorted(glob.glob(pattern), key=natural_sort_key)
    
    if not image_paths:
        print(f"Tidak ada frame ditemukan untuk {exercise_type}")
        return
        
    print(f"Ditemukan {len(image_paths)} frame untuk {exercise_type}. Membangun video demo...")
    
    # Baca frame pertama untuk tahu resolusi
    first_frame = cv2.imread(image_paths[0])
    h, w = first_frame.shape[:2]
    
    # 1. Pipeline Evaluator
    pipeline = BiomechanicalPipeline()
    pipeline.active_mode = mode
    
    raw_video_path = os.path.join(output_dir, f"raw_{exercise_type.lower()}_sample.mp4")
    eval_video_path = os.path.join(output_dir, f"skelio_{exercise_type.lower()}_evaluated.mp4")
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_raw = cv2.VideoWriter(raw_video_path, fourcc, fps, (w, h))
    out_eval = cv2.VideoWriter(eval_video_path, fourcc, fps, (w, h))
    
    # Ulangi sequence 2x agar durasi video pas untuk presentasi (~7-8 detik)
    sequence = image_paths + list(reversed(image_paths)) + image_paths
    
    for i, img_p in enumerate(sequence):
        frame = cv2.imread(img_p)
        if frame is None:
            continue
            
        out_raw.write(frame)
        
        # Proses pipeline SKELIO
        processed = pipeline.process_frame(frame.copy())
        out_eval.write(processed)
        
    out_raw.release()
    out_eval.release()
    print(f"[OK] Video Raw selesai: {raw_video_path}")
    print(f"[OK] Video Evaluasi SKELIO selesai: {eval_video_path}")

if __name__ == "__main__":
    print("Mempersiapkan video demo Push-up dan Squat untuk presentasi Sempro...")
    build_demo_video(exercise_type="Push-up", mode="PUSH-UP", fps=12)
    build_demo_video(exercise_type="Squat", mode="SQUAT", fps=12)
