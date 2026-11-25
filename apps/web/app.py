import os
import sys
import time
import json
import threading
import cv2
import numpy as np
from flask import Flask, render_template, Response, jsonify, request, send_file
import io
import csv

# Pastikan root workspace Bigdata ada di sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.biomechanical_pipeline import BiomechanicalPipeline

DIST_DIR = os.path.join(ROOT_DIR, 'dist')
app = Flask(
    __name__,
    static_folder=os.path.join(DIST_DIR, 'assets') if os.path.exists(DIST_DIR) else os.path.join(BASE_DIR, 'static'),
    static_url_path='/assets' if os.path.exists(DIST_DIR) else '/static',
    template_folder=DIST_DIR if os.path.exists(DIST_DIR) else os.path.join(BASE_DIR, 'templates')
)


@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response


# Folder Penyimpanan Video Upload Pengguna
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global State
pipeline = None
camera_lock = threading.Lock()
current_source = "webcam"
uploaded_filename = None
cap = None
is_running = True
last_frame_bytes = None

# Sesi Latihan & Timer
session_is_active = False
session_start_time = time.time()
session_duration_seconds = 0

# Log Repetisi Sesi Latihan (Big Data In-Memory Logger)
workout_history = []
last_rep_recorded = {}  # {track_id: rep_count}

DEMO_VIDEOS = {
    "pushup_demo": os.path.join(ROOT_DIR, "assets_sempro", "raw_push-up_sample.mp4"),
    "squat_demo": os.path.join(ROOT_DIR, "assets_sempro", "raw_squat_sample.mp4"),
}

def get_pipeline():
    global pipeline
    if pipeline is None:
        candidates = [
            os.path.join(ROOT_DIR, "models", "best_calisthenics_pose.pt"),
            os.path.join(ROOT_DIR, "models", "trained_weights", "yolo11m-pose", "weights", "best.pt"),
            r"C:\Users\Lenovo\Downloads\Dataset Video\training\runs\pose_models\yolo11m-pose\weights\best.pt",
            os.path.join(ROOT_DIR, "yolo11n-pose.pt"),
        ]
        model_path = next((p for p in candidates if os.path.exists(p)), candidates[-1])
        pipeline = BiomechanicalPipeline(pose_model_path=model_path)
    return pipeline

def open_capture(source_key):
    global cap
    if cap is not None:
        try:
            cap.release()
        except Exception:
            pass

    if source_key == "webcam":
        c = cv2.VideoCapture(0)
        c.set(cv2.CAP_PROP_FRAME_WIDTH, 854)
        c.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        c.set(cv2.CAP_PROP_FPS, 30)
    elif source_key in DEMO_VIDEOS:
        video_path = DEMO_VIDEOS[source_key]
        if os.path.exists(video_path):
            c = cv2.VideoCapture(video_path)
        else:
            c = cv2.VideoCapture(0)
    else:
        # File video yang di-upload atau path absolut
        if os.path.exists(source_key):
            c = cv2.VideoCapture(source_key)
        else:
            c = cv2.VideoCapture(0)

    cap = c
    return cap

def stream_worker():
    """Background worker untuk membaca frame video, inferensi AI, dan encode MJPEG."""
    global cap, last_frame_bytes, is_running, current_source, workout_history, last_rep_recorded

    pipe = get_pipeline()
    open_capture(current_source)

    while is_running:
        with camera_lock:
            if cap is None or not cap.isOpened():
                time.sleep(0.05)
                continue

            ret, frame = cap.read()
            if not ret or frame is None:
                # Jika video demo/upload habis, loop kembali ke awal
                if current_source != "webcam":
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    time.sleep(0.03)
                    continue

            # Process frame melalui AI Pipeline SKELIO
            try:
                annotated = pipe.process_frame(frame)
            except Exception as e:
                annotated = frame

            # Catat repetisi baru ke workout_history jika ada penambahan
            now_iso = time.strftime("%H:%M:%S")
            for tid, pstate in pipe.persons.items():
                prev_reps = last_rep_recorded.get(tid, 0)
                if pstate.rep_count > prev_reps:
                    is_clean = (pstate.clean_reps > 0 and not pstate.current_rep_fault)
                    status_text = getattr(pstate, 'status', "BERLATIH")
                    rep_entry = {
                        "id": len(workout_history) + 1,
                        "time": now_iso,
                        "track_id": tid,
                        "exercise": pstate.exercise_mode,
                        "rep_number": pstate.rep_count,
                        "depth_pct": round(float(pstate.depth_pct), 1),
                        "angle_deg": round(float(getattr(pstate, 'primary_angle', 0.0)), 1),
                        "posture_angle": round(float(getattr(pstate, 'posture_angle', 0.0)), 1),
                        "status": "Bersih (Clean)" if is_clean else status_text,
                        "is_clean": is_clean,
                        "raw_fault": status_text if not is_clean else None,
                        "quality_badge": "success" if is_clean else "warning"
                    }
                    workout_history.append(rep_entry)
                    last_rep_recorded[tid] = pstate.rep_count

            # JPEG Compression untuk live web streaming
            ret_enc, buffer = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret_enc:
                last_frame_bytes = buffer.tobytes()

        time.sleep(0.015)  # Cap di ~45 FPS untuk efisiensi CPU

# Mulai worker kamera di background thread
threading.Thread(target=stream_worker, daemon=True).start()

@app.route('/')
def index():
    if os.path.exists(os.path.join(DIST_DIR, 'index.html')):
        return send_file(os.path.join(DIST_DIR, 'index.html'))
    return render_template('index.html')

@app.route('/<path:path>')
def static_proxy(path):
    file_path = os.path.join(DIST_DIR, path)
    if os.path.exists(file_path):
        return send_file(file_path)
    if os.path.exists(os.path.join(DIST_DIR, 'index.html')):
        return send_file(os.path.join(DIST_DIR, 'index.html'))
    return "Not Found", 404


@app.route('/video_feed')
def video_feed():
    def generate():
        global last_frame_bytes
        while is_running:
            if last_frame_bytes is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + last_frame_bytes + b'\r\n')
            time.sleep(0.03)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/telemetry')
def api_telemetry():
    global session_duration_seconds
    pipe = get_pipeline()
    persons_data = []

    primary_person = {
        "track_id": 1,
        "rep_count": 0,
        "clean_reps": 0,
        "bad_reps": 0,
        "depth_pct": 0,
        "stage": "IDLE",
        "status": "Mencari Pose Subjek...",
        "primary_angle": 0.0,
        "posture_angle": 0.0,
        "exercise": pipe.active_mode
    }

    if pipe.persons:
        sorted_p = sorted(pipe.persons.items(), key=lambda x: x[1].rep_count, reverse=True)
        for rank, (tid, ps) in enumerate(sorted_p):
            bad_reps = max(0, ps.rep_count - ps.clean_reps)
            p_dict = {
                "track_id": tid,
                "rank": rank + 1,
                "rep_count": ps.rep_count,
                "clean_reps": ps.clean_reps,
                "bad_reps": bad_reps,
                "depth_pct": round(float(ps.depth_pct), 1),
                "stage": ps.stage,
                "status": getattr(ps, 'status', "BERLATIH"),
                "primary_angle": round(float(getattr(ps, 'primary_angle', 0.0)), 1),
                "posture_angle": round(float(getattr(ps, 'posture_angle', 0.0)), 1),
                "exercise": ps.exercise_mode
            }
            persons_data.append(p_dict)

        primary_person = persons_data[0]

    # Hitung durasi aktif jika sesi latihan berjalan
    if session_is_active:
        active_sec = int(time.time() - session_start_time)
    else:
        active_sec = session_duration_seconds

    return jsonify({
        "status": "online",
        "fps": round(pipe.fps, 1),
        "active_mode": pipe.active_mode,
        "current_source": current_source,
        "uploaded_filename": uploaded_filename,
        "person_count": len(pipe.persons),
        "session_active": session_is_active,
        "session_duration": active_sec,
        "primary": primary_person,
        "persons": persons_data,
        "history_count": len(workout_history)
    })

@app.route('/api/upload_video', methods=['POST'])
def api_upload_video():
    """Endpoint Upload File Video Mandiri (.mp4, .mov, .avi)."""
    global current_source, uploaded_filename, workout_history, last_rep_recorded
    if 'video' not in request.files:
        return jsonify({"success": False, "error": "Tidak ada file video yang dikirim"}), 400

    file = request.files['video']
    if file.filename == '':
        return jsonify({"success": False, "error": "Nama file kosong"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
        return jsonify({"success": False, "error": f"Format {ext} tidak didukung. Gunakan .mp4, .mov, atau .avi"}), 400

    safe_filename = f"user_video_{int(time.time())}{ext}"
    saved_path = os.path.join(UPLOAD_FOLDER, safe_filename)
    file.save(saved_path)

    # Ganti source kamera ke video upload
    with camera_lock:
        current_source = saved_path
        uploaded_filename = file.filename
        open_capture(current_source)

    # Reset reps untuk video baru
    pipe = get_pipeline()
    for tid, ps in pipe.persons.items():
        ps.rep_count = 0
        ps.clean_reps = 0
        ps.stage = "UP"
        ps.depth_pct = 0.0
    last_rep_recorded.clear()

    return jsonify({
        "success": True,
        "filename": file.filename,
        "source": current_source
    })

@app.route('/api/session_start', methods=['POST'])
def api_session_start():
    """Mulai sesi latihan baru (Reset timer dan reps)."""
    global session_is_active, session_start_time, workout_history, last_rep_recorded
    session_is_active = True
    session_start_time = time.time()
    
    pipe = get_pipeline()
    for tid, ps in pipe.persons.items():
        ps.rep_count = 0
        ps.clean_reps = 0
        ps.stage = "UP"
        ps.depth_pct = 0.0
    last_rep_recorded.clear()
    workout_history.clear()

    return jsonify({"success": True, "message": "Sesi latihan dimulai!"})

@app.route('/api/session_stop', methods=['POST'])
def api_session_stop():
    """Selesaikan sesi latihan dan hitung rekapitulasi data."""
    global session_is_active, session_duration_seconds
    if session_is_active:
        session_duration_seconds = int(time.time() - session_start_time)
        session_is_active = False
    return jsonify({"success": True, "duration": session_duration_seconds})

@app.route('/api/session_summary')
def api_session_summary():
    """Menghitung ringkasan evaluasi sesi, skor postur, dan rekomendasi AI."""
    pipe = get_pipeline()
    
    total_reps = 0
    clean_reps = 0
    if pipe.persons:
        primary = max(pipe.persons.values(), key=lambda p: p.rep_count)
        total_reps = primary.rep_count
        clean_reps = primary.clean_reps
    elif workout_history:
        total_reps = len(workout_history)
        clean_reps = sum(1 for r in workout_history if r.get('is_clean', False))

    bad_reps = max(0, total_reps - clean_reps)
    accuracy_pct = round((clean_reps / max(1, total_reps)) * 100, 1)

    # Rata-rata kedalaman gerakan
    depths = [r['depth_pct'] for r in workout_history if 'depth_pct' in r]
    avg_depth = round(sum(depths) / max(1, len(depths)), 1) if depths else 0.0

    # Durasi dan Kalori
    dur_sec = session_duration_seconds if not session_is_active else int(time.time() - session_start_time)
    minutes = max(0.1, dur_sec / 60.0)
    # Estimasi kalori kalistenik (MET ~7.0 untuk push-up/squat moderat)
    calories_burned = round(minutes * 7.2, 1)

    # Perhitungan Skor Postur (0–100)
    if total_reps == 0:
        score = 0
        grade = "N/A (Belum Ada Repetisi)"
        grade_color = "slate"
    else:
        # 65% Rasio Gerakan Bersih + 35% Kedalaman Tercapai (Batas target 70%)
        depth_score = min(35.0, (avg_depth / 70.0) * 35.0)
        clean_score = (clean_reps / total_reps) * 65.0
        score = round(clean_score + depth_score)
        score = min(100, max(0, score))

        if score >= 90:
            grade = "A (Sangat Sempurna)"
            grade_color = "emerald"
        elif score >= 80:
            grade = "B (Bagus & Konsisten)"
            grade_color = "cyan"
        elif score >= 70:
            grade = "C (Cukup / Perlu Perbaikan)"
            grade_color = "amber"
        else:
            grade = "D (Perlu Bimbingan Postur)"
            grade_color = "rose"

    # Analisis Rekomendasi Cerdas AI
    recommendations = []
    faults = [r.get('raw_fault') for r in workout_history if r.get('raw_fault')]
    fault_counts = {}
    for f in faults:
        if f:
            fault_counts[f] = fault_counts.get(f, 0) + 1

    if total_reps == 0:
        recommendations.append("Mulai lakukan gerakan di depan kamera untuk mendapatkan evaluasi analitik biomekanik.")
    else:
        if avg_depth < 65.0:
            recommendations.append("Kedalaman gerakan rata-rata masih dangkal (<70%). Usahakan sendi siku atau lutut ditekuk hingga mencapai sudut 90°.")
        else:
            recommendations.append("Kedalaman gerakan sangat konsisten di zona optimal (>70%). Pertahankan rentang gerak (Range of Motion) ini.")

        if any("PINGGUL" in str(k) for k in fault_counts):
            recommendations.append("Terdeteksi pinggul terlalu turun (Hip Sagging). Kencangkan otot perut (core) dan gluteus agar tulang belakang lurus sejajar.")
        
        if any("BUNGKUK" in str(k) for k in fault_counts):
            recommendations.append("Saat posisi bawah squat, dada cenderung membungkuk ke depan. Busungkan dada dan jaga pandangan lurus ke depan.")

        if clean_reps == total_reps and total_reps >= 5:
            recommendations.append("Performa luar biasa! Seluruh repetisi berhasil dieksekusi dengan postur biomekanika yang sangat bersih tanpa cacat form.")

    return jsonify({
        "exercise": pipe.active_mode,
        "total_reps": total_reps,
        "clean_reps": clean_reps,
        "bad_reps": bad_reps,
        "accuracy_pct": accuracy_pct,
        "avg_depth": avg_depth,
        "duration_seconds": dur_sec,
        "duration_formatted": f"{dur_sec // 60:02d}:{dur_sec % 60:02d}",
        "calories_burned": calories_burned,
        "score": score,
        "grade": grade,
        "grade_color": grade_color,
        "recommendations": recommendations,
        "fault_summary": fault_counts
    })

@app.route('/api/set_mode', methods=['POST'])
def api_set_mode():
    pipe = get_pipeline()
    data = request.get_json() or {}
    new_mode = data.get('mode', 'PUSH-UP').upper()
    if new_mode in ["PUSH-UP", "SQUAT", "SIT-UP", "AUTO"]:
        pipe.active_mode = new_mode
        return jsonify({"success": True, "active_mode": pipe.active_mode})
    return jsonify({"success": False, "error": "Invalid mode"}), 400

@app.route('/api/set_source', methods=['POST'])
def api_set_source():
    global current_source, uploaded_filename
    data = request.get_json() or {}
    new_source = data.get('source', 'webcam')
    with camera_lock:
        current_source = new_source
        if new_source in ["webcam", "pushup_demo", "squat_demo"]:
            uploaded_filename = None
        open_capture(current_source)
    return jsonify({"success": True, "current_source": current_source})

@app.route('/api/reset_reps', methods=['POST'])
def api_reset_reps():
    global workout_history, last_rep_recorded
    pipe = get_pipeline()
    for tid, ps in pipe.persons.items():
        ps.rep_count = 0
        ps.clean_reps = 0
        ps.stage = "UP"
        ps.depth_pct = 0.0
    last_rep_recorded.clear()
    return jsonify({"success": True, "message": "Reps berhasil di-reset"})

@app.route('/api/clear_history', methods=['POST'])
def api_clear_history():
    global workout_history
    workout_history.clear()
    return jsonify({"success": True, "message": "Riwayat sesi berhasil dibersihkan"})

@app.route('/api/history')
def api_history():
    return jsonify({"history": workout_history[::-1][:50]})

@app.route('/api/export_history')
def api_export_history():
    """Ekspor log sesi latihan ke format CSV (Karakteristik Big Data)."""
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["ID", "Timestamp", "Person_Track_ID", "Exercise", "Rep_Number", "Depth_Percentage", "Joint_Angle_Deg", "Status"])
    for row in workout_history:
        cw.writerow([
            row["id"], row["time"], row["track_id"], row["exercise"],
            row["rep_number"], row["depth_pct"], row["angle_deg"], row["status"]
        ])
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name=f"skelio_workout_log_{int(time.time())}.csv")

if __name__ == '__main__':
    port = 5000
    print(f"🚀 SKELIO Web Application siap berjalan di: http://localhost:{port}")
    
    # Buka browser otomatis saat server sudah dipastikan aktif dan siap
    def open_browser_when_ready():
        time.sleep(1.5)
        import webbrowser
        webbrowser.open(f"http://localhost:{port}")
    
    threading.Thread(target=open_browser_when_ready, daemon=True).start()
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
