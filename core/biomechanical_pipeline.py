"""
SISTEM SKELIO: REAL-TIME BIOMECHANICAL ANALYSIS PIPELINE
Metode: YOLOv11-Pose + ByteTrack + One-Euro Filter + Kinematic Angular Geometry + FSM Rep Counter
Mendukung Gerakan: Push-Up, Squat, dan Sit-Up (Multi-Person Maks. 3 Orang)
Proposal Penelitian: Teknik Informatika UNESA 2026 (Kelompok 11 Big Data)
"""

import os
import sys
import time
import math
import cv2
import numpy as np
import torch
import threading
from ultralytics import YOLO


# ==============================================================================
# 1. ONE-EURO FILTER (ADAPTIVE VIBRATION & JITTER SMOOTHER)
# ==============================================================================
class OneEuroFilter:
    """
    Industry-Standard One-Euro Filter (Digunakan pada MediaPipe, ARKit, OpenPose).
    Meredam jitter statis dan lag pergerakan cepat secara dinamis.
    """
    def __init__(self, min_cutoff=0.8, beta=0.005, d_cutoff=1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_prev = None
        self.dx_prev = None
        self.t_prev = None

    def _smoothing_factor(self, t_e, cutoff):
        r = 2 * math.pi * cutoff * t_e
        return r / (r + 1.0)

    def _exponential_smoothing(self, a, x, x_prev):
        return a * x + (1.0 - a) * x_prev

    def filter(self, x, timestamp=None):
        if timestamp is None:
            timestamp = time.time()

        if self.x_prev is None or self.x_prev.shape != x.shape:
            self.t_prev = timestamp
            self.x_prev = x.copy()
            self.dx_prev = np.zeros_like(x)
            return x.copy()

        t_e = max(1e-5, timestamp - self.t_prev)
        self.t_prev = timestamp

        a_d = self._smoothing_factor(t_e, self.d_cutoff)
        dx = (x - self.x_prev) / t_e
        dx_hat = self._exponential_smoothing(a_d, dx, self.dx_prev)
        self.dx_prev = dx_hat

        cutoff = self.min_cutoff + self.beta * np.abs(dx_hat)
        a = self._smoothing_factor(t_e, cutoff)
        x_hat = self._exponential_smoothing(a, x, self.x_prev)
        self.x_prev = x_hat
        return x_hat

    def reset(self):
        self.x_prev = None
        self.dx_prev = None
        self.t_prev = None


# ==============================================================================
# 2. PALM CENTER TRACKER (ESTIMASI TITIK TELAPAK TANGAN DARI VEKTOR LENGAN)
# ==============================================================================
class PalmCenterTracker:
    """
    Tracker Pusat Telapak Tangan (Palm Center).
    Menghitung pusat telapak dari vektor perpanjangan siku ke pergelangan tangan (35%).
    """
    def __init__(self):
        self.smoothers = {
            "Left": OneEuroFilter(min_cutoff=0.7, beta=0.01),
            "Right": OneEuroFilter(min_cutoff=0.7, beta=0.01)
        }

    def extract_hands(self, frame, body_keypoints, confidences):
        if body_keypoints is None or confidences is None:
            for s in self.smoothers.values():
                s.reset()
            return []

        detected = []
        wrist_indices = [
            (9, "Left", 7),
            (10, "Right", 8)
        ] if len(body_keypoints) == 17 else [
            (4, "Left", 3),
            (6, "Right", 5)
        ]

        active = set()
        for w_idx, label, e_idx in wrist_indices:
            if w_idx < len(body_keypoints) and confidences[w_idx] >= 0.35:
                active.add(label)
                wx, wy = body_keypoints[w_idx]

                if e_idx < len(body_keypoints) and confidences[e_idx] >= 0.35:
                    ex, ey = body_keypoints[e_idx]
                    dx, dy = float(wx - ex), float(wy - ey)
                    length = max(1e-5, math.hypot(dx, dy))
                    palm_x = float(wx) + (dx / length) * (length * 0.35)
                    palm_y = float(wy) + (dy / length) * (length * 0.35)
                else:
                    palm_x, palm_y = float(wx), float(wy) - 35.0

                palm_pt = np.array([[palm_x, palm_y]], dtype=np.float32)
                if label in self.smoothers:
                    palm_pt = self.smoothers[label].filter(palm_pt)

                px, py = float(palm_pt[0, 0]), float(palm_pt[0, 1])
                detected.append({
                    'label': label,
                    'wrist': np.array([float(wx), float(wy)]),
                    'palm_center': np.array([px, py]),
                    'score': confidences[w_idx]
                })

        for key in self.smoothers:
            if key not in active:
                self.smoothers[key].reset()

        return detected


# ==============================================================================
# 3. THREADED WEBCAM READER (LOW LATENCY 0ms QUEUE FLUSHING)
# ==============================================================================
class ThreadedWebcam:
    def __init__(self, src=0):
        self.cap = cv2.VideoCapture(src)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 854)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.grabbed, self.frame = self.cap.read()
        else:
            self.grabbed, self.frame = False, None
            
        self.stopped = False
        self.lock = threading.Lock()
        
    def start(self):
        if self.cap.isOpened():
            t = threading.Thread(target=self.update, daemon=True)
            t.start()
        return self
        
    def update(self):
        while not self.stopped:
            if not self.cap.isOpened():
                break
            self.cap.grab()
            ret, frame = self.cap.retrieve()
            if ret and frame is not None:
                with self.lock:
                    self.grabbed = ret
                    self.frame = frame

    def read(self):
        with self.lock:
            return self.grabbed, (self.frame.copy() if self.frame is not None else None)

    def isOpened(self):
        return self.cap is not None and self.cap.isOpened() and not self.stopped

    def release(self):
        self.stopped = True
        if self.cap is not None:
            self.cap.release()


# ==============================================================================
# 4. PERSON STATE (MULTI-PERSON TRACKING & FINITE STATE MACHINE)
# ==============================================================================
_PERSON_COLORS = [
    (0, 230, 255),    # Person 1 — Kuning Cyan
    (80, 255, 80),    # Person 2 — Hijau Neon
    (0, 140, 255),    # Person 3 — Orange
]

class PersonState:
    def __init__(self):
        self.smoother      = OneEuroFilter(min_cutoff=0.8, beta=0.005)
        self.hand_tracker  = PalmCenterTracker()
        self.rep_count     = 0
        self.clean_reps    = 0
        self.current_rep_fault = False
        self.stage         = "UP"
        self._depth_buffer = []
        self.depth_pct     = 0.0
        self.last_seen     = time.time()
        self.exercise_mode = "PUSH-UP"


# ==============================================================================
# 5. CORE BIOMECHANICAL PIPELINE (SISTEM SKELIO)
# ==============================================================================
class BiomechanicalPipeline:
    def __init__(self, pose_model_path=None, tracker_yaml=None):
        self.device = 0 if torch.cuda.is_available() else 'cpu'
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(base_dir) if os.path.basename(base_dir) == 'core' else base_dir
        
        default_model = os.path.join(base_dir, "yolo11n-pose.pt")
        if not os.path.exists(default_model):
            default_model = os.path.join(root_dir, "yolo11n-pose.pt")
            
        trained_model = os.path.join(base_dir, "models", "best_calisthenics_pose.pt")
        if not os.path.exists(trained_model):
            trained_model = os.path.join(root_dir, "models", "best_calisthenics_pose.pt")
        
        if pose_model_path and os.path.exists(pose_model_path):
            target_model = pose_model_path
        elif os.path.exists(trained_model):
            target_model = trained_model
        elif os.path.exists(default_model):
            target_model = default_model
        else:
            target_model = "yolo11n-pose.pt"
            
        print(f"📦 SKELIO: Memuat Model Pose dari: {target_model} (Device: {self.device})")
        self.detector = YOLO(target_model)
        
        default_yaml = os.path.join(base_dir, "bytetrack_live.yaml")
        if not os.path.exists(default_yaml):
            default_yaml = os.path.join(root_dir, "core", "bytetrack_live.yaml")
        self._tracker_yaml_path = tracker_yaml if (tracker_yaml and os.path.exists(tracker_yaml)) else default_yaml

        self.persons        = {}
        self.MAX_PERSONS    = 3
        self.PERSON_TIMEOUT = 5.0
        
        # Mode Latihan Aktif Global: 'PUSH-UP', 'SQUAT', 'SIT-UP', 'AUTO'
        self.active_mode = "PUSH-UP"

        self.prev_time   = time.time()
        self.fps         = 0.0
        self._fps_buffer = []

    def calculate_angle(self, A, B, C):
        """Hukum Kosinus untuk menghitung sudut 2D pada sendi B."""
        a = math.dist(B, C)
        c = math.dist(A, B)
        b = math.dist(A, C)
        if a == 0 or c == 0:
            return 0.0
        cos_val = (a**2 + c**2 - b**2) / (2 * a * c)
        return math.degrees(math.acos(np.clip(cos_val, -1.0, 1.0)))

    def draw_angle_arc(self, frame, A, B, C, color=(0, 255, 255), radius=28):
        """Menggambar visualisasi busur sudut."""
        try:
            angA = math.degrees(math.atan2(A[1] - B[1], A[0] - B[0]))
            angC = math.degrees(math.atan2(C[1] - B[1], C[0] - B[0]))
            start_ang, end_ang = min(angA, angC), max(angA, angC)
            if end_ang - start_ang > 180:
                start_ang, end_ang = end_ang, start_ang + 360
            overlay = frame.copy()
            cv2.ellipse(overlay, (int(B[0]), int(B[1])), (radius, radius), 0, start_ang, end_ang, color, -1)
            cv2.addWeighted(overlay, 0.40, frame, 0.60, 0, frame)
            cv2.ellipse(frame, (int(B[0]), int(B[1])), (radius, radius), 0, start_ang, end_ang, color, 2, cv2.LINE_AA)
        except Exception:
            pass

    def detect_exercise_auto(self, keypoints, confidences):
        """Mendeteksi jenis gerakan secara otomatis berdasarkan orientasi tubuh."""
        if len(keypoints) == 17:
            sh, hip, kne = 5, 11, 13
        else:
            sh, hip, kne = 1, 7, 9
            
        if confidences[sh] > 0.4 and confidences[hip] > 0.4:
            dx = abs(keypoints[sh][0] - keypoints[hip][0])
            dy = abs(keypoints[sh][1] - keypoints[hip][1])
            if dy > dx * 1.3:
                return "SQUAT"
            else:
                if keypoints[sh][1] > keypoints[kne][1] - 30:
                    return "SIT-UP"
                return "PUSH-UP"
        return "PUSH-UP"

    def stage1_extract_and_smooth(self, frame):
        try:
            results = self.detector.track(
                frame,
                device=self.device,
                imgsz=480,
                conf=0.35,
                persist=True,
                verbose=False,
                tracker=self._tracker_yaml_path
            )
        except Exception:
            results = self.detector.predict(
                frame,
                device=self.device,
                imgsz=480,
                conf=0.35,
                verbose=False
            )

        if not results or len(results[0].keypoints) == 0:
            return []

        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            return []

        confs = boxes.conf.cpu().numpy()
        tids = boxes.id.int().cpu().numpy() if boxes.id is not None else np.arange(len(confs), dtype=int)
        order = np.argsort(confs)[::-1][:self.MAX_PERSONS]

        now = time.time()
        detected = []

        for rank, idx in enumerate(order):
            tid = int(tids[idx])
            kpt_data = results[0].keypoints[idx]
            if kpt_data.xy is None or kpt_data.xy.shape[1] == 0:
                continue

            keypoints = kpt_data.xy[0].cpu().numpy()
            confidences = (kpt_data.conf[0].cpu().numpy() if kpt_data.conf is not None else np.ones(len(keypoints)))

            if tid not in self.persons:
                self.persons[tid] = PersonState()

            pstate = self.persons[tid]
            pstate.last_seen = now
            smoothed = pstate.smoother.filter(keypoints)

            detected.append({
                'track_id': tid,
                'rank': rank,
                'keypoints': smoothed,
                'confidences': confidences,
            })

        stale = [t for t, ps in self.persons.items() if (now - ps.last_seen) > self.PERSON_TIMEOUT]
        for t in stale:
            del self.persons[t]

        return detected

    def stage3_visualize_and_evaluate(self, keypoints, confidences, hands_data, frame, pstate, person_rank):
        p_color = _PERSON_COLORS[min(person_rank, len(_PERSON_COLORS) - 1)]
        h, w = frame.shape[:2]

        if len(keypoints) == 17:
            skeleton_limbs = [
                (0, 1), (0, 2), (1, 3), (2, 4),
                (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
                (5, 11), (6, 12), (11, 12),
                (11, 13), (13, 15), (12, 14), (14, 16)
            ]
            k_sh_l, k_elb_l, k_wri_l, k_hip_l, k_kne_l, k_ank_l = 5, 7, 9, 11, 13, 15
            k_sh_r, k_elb_r, k_wri_r, k_hip_r, k_kne_r, k_ank_r = 6, 8, 10, 12, 14, 16
        else:
            skeleton_limbs = [
                (0, 1), (0, 2), (1, 2), (1, 3), (3, 4), (2, 5), (5, 6),
                (1, 7), (2, 8), (7, 8), (7, 9), (9, 11), (8, 10), (10, 12)
            ]
            k_sh_l, k_elb_l, k_wri_l, k_hip_l, k_kne_l, k_ank_l = 1, 3, 4, 7, 9, 11
            k_sh_r, k_elb_r, k_wri_r, k_hip_r, k_kne_r, k_ank_r = 2, 5, 6, 8, 10, 12

        def is_valid_pt(idx):
            if idx >= len(keypoints) or confidences[idx] < 0.35:
                return False
            x, y = keypoints[idx]
            return 2 <= x < (w - 2) and 2 <= y < (h - 2)

        # 1. Bounding Box
        valid_indices = [i for i in range(len(keypoints)) if is_valid_pt(i)]
        if len(valid_indices) >= 4:
            pts = keypoints[valid_indices]
            bx_min, by_min = max(0, int(np.min(pts[:, 0])) - 15), max(0, int(np.min(pts[:, 1])) - 20)
            bx_max, by_max = min(w - 1, int(np.max(pts[:, 0])) + 15), min(h - 1, int(np.max(pts[:, 1])) + 15)
            cv2.rectangle(frame, (bx_min, by_min), (bx_max, by_max), (0, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, f"SKELETON {person_rank + 1}", (bx_min + 5, by_min - 8),
                        cv2.FONT_HERSHEY_DUPLEX, 0.45, p_color, 1, cv2.LINE_AA)

        # 2. Limbs & Keypoints
        for p1, p2 in skeleton_limbs:
            if is_valid_pt(p1) and is_valid_pt(p2):
                pt1 = (int(keypoints[p1][0]), int(keypoints[p1][1]))
                pt2 = (int(keypoints[p2][0]), int(keypoints[p2][1]))
                cv2.line(frame, pt1, pt2, p_color, 2, cv2.LINE_AA)

        for i in valid_indices:
            x, y = int(keypoints[i][0]), int(keypoints[i][1])
            cv2.circle(frame, (x, y), 5, p_color, -1, cv2.LINE_AA)
            cv2.circle(frame, (x, y), 6, (0, 0, 0), 1, cv2.LINE_AA)

        # 3. Palm Center
        for hand in hands_data:
            wx, wy = int(hand['wrist'][0]), int(hand['wrist'][1])
            px, py = int(hand['palm_center'][0]), int(hand['palm_center'][1])
            cv2.line(frame, (wx, wy), (px, py), (255, 255, 0), 2, cv2.LINE_AA)
            cv2.circle(frame, (px, py), 7, (0, 255, 0), -1, cv2.LINE_AA)

        # Mode Gerakan
        curr_mode = self.active_mode
        if curr_mode == "AUTO":
            curr_mode = self.detect_exercise_auto(keypoints, confidences)
        pstate.exercise_mode = curr_mode

        status = "POSISIKAN TUBUH TERLIHAT"
        stat_color = (0, 255, 255)
        primary_angle = 0.0
        posture_angle = 0.0

        # PUSH-UP
        if curr_mode == "PUSH-UP":
            elbow_angles = []
            if is_valid_pt(k_sh_l) and is_valid_pt(k_elb_l) and is_valid_pt(k_wri_l):
                ang_l = self.calculate_angle(keypoints[k_sh_l], keypoints[k_elb_l], keypoints[k_wri_l])
                elbow_angles.append(ang_l)
                self.draw_angle_arc(frame, keypoints[k_sh_l], keypoints[k_elb_l], keypoints[k_wri_l], (255, 0, 255))
            if is_valid_pt(k_sh_r) and is_valid_pt(k_elb_r) and is_valid_pt(k_wri_r):
                ang_r = self.calculate_angle(keypoints[k_sh_r], keypoints[k_elb_r], keypoints[k_wri_r])
                elbow_angles.append(ang_r)
                self.draw_angle_arc(frame, keypoints[k_sh_r], keypoints[k_elb_r], keypoints[k_wri_r], (200, 0, 255))

            if elbow_angles:
                primary_angle = sum(elbow_angles) / len(elbow_angles)
                # Koreksi Depth Bar: Turun mendekati 85° = 100% kedalaman tercapai (bukan terbalik)
                pstate.depth_pct = max(0.0, min(100.0, (160.0 - primary_angle) / (160.0 - 85.0) * 100.0))

                if primary_angle < 90 and pstate.stage == "UP":
                    pstate.stage = "DOWN"
                if primary_angle > 155 and pstate.stage == "DOWN":
                    pstate.stage = "UP"
                    pstate.rep_count += 1
                    if not pstate.current_rep_fault:
                        pstate.clean_reps += 1
                    pstate.current_rep_fault = False

            ref_leg = k_ank_l if is_valid_pt(k_ank_l) else (k_kne_l if is_valid_pt(k_kne_l) else None)
            if ref_leg and is_valid_pt(k_sh_l) and is_valid_pt(k_hip_l):
                posture_angle = self.calculate_angle(keypoints[k_sh_l], keypoints[k_hip_l], keypoints[ref_leg])
                self.draw_angle_arc(frame, keypoints[k_sh_l], keypoints[k_hip_l], keypoints[ref_leg], (0, 255, 255))
                if posture_angle > 165:
                    status = "POSTUR SEMPURNA"
                    stat_color = (0, 255, 0)
                elif posture_angle > 148:
                    status = "POSTUR BAIK"
                    stat_color = (0, 255, 255)
                else:
                    status = "PINGGUL TERLALU TURUN!"
                    stat_color = (0, 0, 255)
                    pstate.current_rep_fault = True

        # SQUAT
        elif curr_mode == "SQUAT":
            knee_angles = []
            if is_valid_pt(k_hip_l) and is_valid_pt(k_kne_l) and is_valid_pt(k_ank_l):
                ang_k_l = self.calculate_angle(keypoints[k_hip_l], keypoints[k_kne_l], keypoints[k_ank_l])
                knee_angles.append(ang_k_l)
                self.draw_angle_arc(frame, keypoints[k_hip_l], keypoints[k_kne_l], keypoints[k_ank_l], (255, 0, 255))
            if is_valid_pt(k_hip_r) and is_valid_pt(k_kne_r) and is_valid_pt(k_ank_r):
                ang_k_r = self.calculate_angle(keypoints[k_hip_r], keypoints[k_kne_r], keypoints[k_ank_r])
                knee_angles.append(ang_k_r)
                self.draw_angle_arc(frame, keypoints[k_hip_r], keypoints[k_kne_r], keypoints[k_ank_r], (200, 0, 255))

            if knee_angles:
                primary_angle = sum(knee_angles) / len(knee_angles)
                # Koreksi Depth Bar: Turun mendekati 95° = 100% kedalaman tercapai (bukan terbalik)
                pstate.depth_pct = max(0.0, min(100.0, (165.0 - primary_angle) / (165.0 - 95.0) * 100.0))

                if primary_angle < 100 and pstate.stage == "UP":
                    pstate.stage = "DOWN"
                if primary_angle > 155 and pstate.stage == "DOWN":
                    pstate.stage = "UP"
                    pstate.rep_count += 1
                    if not pstate.current_rep_fault:
                        pstate.clean_reps += 1
                    pstate.current_rep_fault = False

            if is_valid_pt(k_sh_l) and is_valid_pt(k_hip_l) and is_valid_pt(k_kne_l):
                posture_angle = self.calculate_angle(keypoints[k_sh_l], keypoints[k_hip_l], keypoints[k_kne_l])
                if posture_angle > 65:
                    status = "SQUAT BAGUS (DADA TEGAK)"
                    stat_color = (0, 255, 0)
                else:
                    status = "BUNGKUK! TEGAKKAN DADA"
                    stat_color = (0, 0, 255)
                    pstate.current_rep_fault = True

        # SIT-UP
        elif curr_mode == "SIT-UP":
            situp_angles = []
            if is_valid_pt(k_sh_l) and is_valid_pt(k_hip_l) and is_valid_pt(k_kne_l):
                ang_s_l = self.calculate_angle(keypoints[k_sh_l], keypoints[k_hip_l], keypoints[k_kne_l])
                situp_angles.append(ang_s_l)
                self.draw_angle_arc(frame, keypoints[k_sh_l], keypoints[k_hip_l], keypoints[k_kne_l], (255, 0, 255))
            if is_valid_pt(k_sh_r) and is_valid_pt(k_hip_r) and is_valid_pt(k_kne_r):
                ang_s_r = self.calculate_angle(keypoints[k_sh_r], keypoints[k_hip_r], keypoints[k_kne_r])
                situp_angles.append(ang_s_r)
                self.draw_angle_arc(frame, keypoints[k_sh_r], keypoints[k_hip_r], keypoints[k_kne_r], (200, 0, 255))

            if situp_angles:
                primary_angle = sum(situp_angles) / len(situp_angles)
                pstate.depth_pct = max(0.0, min(100.0, (130.0 - primary_angle) / 75.0 * 100.0))

                if primary_angle < 65 and pstate.stage == "DOWN":
                    pstate.stage = "UP"
                    pstate.rep_count += 1
                    pstate.clean_reps += 1
                if primary_angle > 125 and pstate.stage == "UP":
                    pstate.stage = "DOWN"

                if pstate.stage == "UP":
                    status = "KONTRAKSI PENUH (SEMPURNA)"
                    stat_color = (0, 255, 0)
                else:
                    status = "REBAH / PERSIAPAN NAIK"
                    stat_color = (0, 255, 255)

        # 4. HUD Card
        hud_w, hud_h = 250, 145
        hud_x = max(10, w - hud_w - 12)
        hud_y = 12 + person_rank * (hud_h + 8)

        overlay = frame.copy()
        cv2.rectangle(overlay, (hud_x, hud_y), (hud_x + hud_w, hud_y + hud_h), (15, 15, 20), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
        cv2.rectangle(frame, (hud_x, hud_y), (hud_x + hud_w, hud_y + hud_h), p_color, 2)

        cv2.putText(frame, f"P{person_rank+1} SKELIO BIOMECHANICS", (hud_x + 8, hud_y + 18),
                    cv2.FONT_HERSHEY_DUPLEX, 0.40, p_color, 1, cv2.LINE_AA)
        cv2.putText(frame, f"REPS: {pstate.rep_count} (Clean:{pstate.clean_reps})", (hud_x + 8, hud_y + 42),
                    cv2.FONT_HERSHEY_DUPLEX, 0.52, (0, 255, 0), 1, cv2.LINE_AA)
        cv2.putText(frame, f"{pstate.stage}", (hud_x + 180, hud_y + 42),
                    cv2.FONT_HERSHEY_DUPLEX, 0.52, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f"GERAK: {curr_mode}", (hud_x + 8, hud_y + 63),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, f"STAT : {status[:25]}", (hud_x + 8, hud_y + 81),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.34, stat_color, 1, cv2.LINE_AA)
        cv2.putText(frame, f"SUDUT: {int(primary_angle)} deg", (hud_x + 8, hud_y + 99),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.34, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, f"FPS  : {self.fps:.1f}", (hud_x + 8, hud_y + 116),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.34, (0, 255, 0), 1, cv2.LINE_AA)
        cv2.putText(frame, "[1:Push 2:Squat 3:Sit A:Auto R:Reset]", (hud_x + 8, hud_y + 134),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.28, (180, 180, 180), 1, cv2.LINE_AA)

        # 5. Depth Indicator Bar
        bar_w = 20
        bar_h = 150
        bar_x = w - 35 - person_rank * 38
        bar_y_top = h - bar_h - 45

        cv2.rectangle(frame, (bar_x, bar_y_top), (bar_x + bar_w, bar_y_top + bar_h), (50, 50, 50), -1)
        cv2.rectangle(frame, (bar_x, bar_y_top), (bar_x + bar_w, bar_y_top + bar_h), p_color, 1)

        cur_depth = pstate.depth_pct
        bar_color = (0, 255, 0) if cur_depth > 70 else ((0, 200, 255) if cur_depth > 35 else (0, 0, 255))
        fill_h = int(bar_h * (cur_depth / 100.0))
        cv2.rectangle(frame, (bar_x, bar_y_top + bar_h - fill_h), (bar_x + bar_w, bar_y_top + bar_h), bar_color, -1)
        cv2.putText(frame, f"{int(cur_depth)}%", (bar_x - 4, bar_y_top + bar_h + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, bar_color, 1, cv2.LINE_AA)

        return frame

    def process_frame(self, frame):
        now = time.time()
        self.fps = 1.0 / max(1e-5, now - self.prev_time)
        self.prev_time = now

        persons_list = self.stage1_extract_and_smooth(frame)
        if not persons_list:
            cv2.putText(frame, f"SISTEM SKELIO [Mode: {self.active_mode}]", (20, 35),
                        cv2.FONT_HERSHEY_DUPLEX, 0.65, (0, 255, 255), 2)
            cv2.putText(frame, "Mencari Pose Subjek...", (20, 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
            cv2.putText(frame, f"FPS: {self.fps:.1f}", (20, 95),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1)
            return frame

        for person in persons_list:
            tid = person['track_id']
            rank = person['rank']
            kpts = person['keypoints']
            conf = person['confidences']
            pstate = self.persons[tid]

            hands_data = pstate.hand_tracker.extract_hands(frame, kpts, conf)
            frame = self.stage3_visualize_and_evaluate(kpts, conf, hands_data, frame, pstate, rank)

        return frame


# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================
if __name__ == "__main__":
    video_source = 0
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        video_source = int(arg) if arg.isdigit() else arg

    pipeline = BiomechanicalPipeline()
    webcam = ThreadedWebcam(video_source).start()

    window_name = "Sistem SKELIO - Evaluasi Kinematik Real-Time (UNESA)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1280, 720)

    print("\n" + "=" * 65)
    print("SISTEM SKELIO: EVALUASI POSTUR OLAHRAGA REAL-TIME AKTIF")
    print("=" * 65)
    print("Tombol Kontrol Keyboard:")
    print("  [1] : Pindah ke Mode PUSH-UP")
    print("  [2] : Pindah ke Mode SQUAT")
    print("  [3] : Pindah ke Mode SIT-UP")
    print("  [A] : Mode AUTO (Deteksi Orientasi Otomatis)")
    print("  [R] : Reset Hitungan Repetisi (Reps = 0)")
    print("  [Q] : Keluar dari Aplikasi")
    print("=" * 65 + "\n")

    while webcam.isOpened():
        ret, frame = webcam.read()
        if not ret or frame is None:
            time.sleep(0.01)
            continue

        output = pipeline.process_frame(frame)
        cv2.imshow(window_name, output)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('Q') or key == 27:
            break
        elif key == ord('1'):
            pipeline.active_mode = "PUSH-UP"
            print(">> Mode Latihan: PUSH-UP")
        elif key == ord('2'):
            pipeline.active_mode = "SQUAT"
            print(">> Mode Latihan: SQUAT")
        elif key == ord('3'):
            pipeline.active_mode = "SIT-UP"
            print(">> Mode Latihan: SIT-UP")
        elif key == ord('a') or key == ord('A'):
            pipeline.active_mode = "AUTO"
            print(">> Mode Latihan: AUTO DETECTION")
        elif key == ord('r') or key == ord('R'):
            for p in pipeline.persons.values():
                p.rep_count = 0
            print(">> Repetisi di-reset ke 0!")

    webcam.release()
    cv2.destroyAllWindows()
