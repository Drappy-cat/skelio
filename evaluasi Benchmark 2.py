import os
import sys
import time
import math
import cv2
import numpy as np
import torch
from ultralytics import YOLO

# Pastikan output konsol Windows aman dari UnicodeEncodeError
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Fallback progress bar jika tqdm tidak terinstall
try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, desc="Memproses", total=None):
        items = list(iterable) if total is None else range(total)
        tot = len(items) if total is None else total
        for idx, item in enumerate(items, start=1):
            pct = (idx / tot) * 100 if tot > 0 else 0
            bar_len = 25
            filled = int(bar_len * idx / tot) if tot > 0 else 0
            bar = "=" * filled + "-" * (bar_len - filled)
            print(f"\r[{desc}] [{bar}] {idx}/{tot} ({pct:.1f}%)", end="", flush=True)
            yield item
        print()


# ==============================================================================
# 1. ENHANCED ONE-EURO FILTER (ANTI-JITTER TINGKAT LANJUT & CONFIDENCE GATED)
# ==============================================================================
class OneEuroFilter:
    """
    Industry-Standard One-Euro Filter (MediaPipe/OpenPose) yang dioptimalkan:
    - min_cutoff = 0.04 (Sangat stabil saat diam/menahan beban, bebas jitter)
    - beta = 0.005 (Responsif tanpa delay saat gerakan cepat)
    - Confidence Gating: Memblokir koordinat drop (0,0) agar tidak melompat.
    """
    def __init__(self, min_cutoff=0.04, beta=0.005, d_cutoff=0.5):
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

    def filter(self, x, conf=None, timestamp=None, min_conf=0.15):
        if timestamp is None:
            timestamp = time.time()

        if self.x_prev is None or self.x_prev.shape != x.shape:
            self.t_prev = timestamp
            self.x_prev = x.copy()
            self.dx_prev = np.zeros_like(x)
            return x.copy()

        t_e = max(1e-5, timestamp - self.t_prev)
        self.t_prev = timestamp

        # Anti-Jitter & Anti-Blink: Confidence Gating
        # Jika keypoint terhalang / confidence < min_conf / bernilai (0, 0),
        # pertahankan koordinat x_prev agar filter TIDAK melompat ke (0, 0)
        x_filtered = x.copy()
        if conf is not None:
            is_invalid = (conf < min_conf) | ((x[:, 0] == 0) & (x[:, 1] == 0))
            x_filtered = np.where(is_invalid[:, None], self.x_prev, x_filtered)

        # Jika titik sebelumnya masih (0, 0) dan sekarang sudah valid,
        # langsung snap ke posisi valid tanpa ditarik dari (0, 0)
        prev_was_zero = (self.x_prev[:, 0] == 0) & (self.x_prev[:, 1] == 0)
        curr_is_valid = ~((x_filtered[:, 0] == 0) & (x_filtered[:, 1] == 0))
        snap_mask = prev_was_zero & curr_is_valid
        if np.any(snap_mask):
            self.x_prev[snap_mask] = x_filtered[snap_mask]
            self.dx_prev[snap_mask] = 0.0

        # Hitung turunan kecepatan pergerakan
        a_d = self._smoothing_factor(t_e, self.d_cutoff)
        dx = (x_filtered - self.x_prev) / t_e
        dx_hat = self._exponential_smoothing(a_d, dx, self.dx_prev)
        self.dx_prev = dx_hat

        # Cutoff frekuensi adaptif
        cutoff = self.min_cutoff + self.beta * np.abs(dx_hat)
        a = self._smoothing_factor(t_e, cutoff)
        x_hat = self._exponential_smoothing(a, x_filtered, self.x_prev)
        self.x_prev = x_hat
        return x_hat

    def reset(self):
        self.x_prev = None
        self.dx_prev = None
        self.t_prev = None


# ==============================================================================
# 2. TRACKER TELAPAK TANGAN (PALM CENTER TRACKER)
# ==============================================================================
class PalmCenterTracker:
    """
    Menghitung pusat telapak tangan (Palm Center) berdasarkan vektor siku -> pergelangan tangan.
    """
    def __init__(self):
        self.smoothers = {
            "Left": OneEuroFilter(min_cutoff=0.04, beta=0.005),
            "Right": OneEuroFilter(min_cutoff=0.04, beta=0.005)
        }

    def extract_hands(self, body_keypoints, confidences, timestamp=None):
        if body_keypoints is None or confidences is None:
            for s in self.smoothers.values():
                s.reset()
            return []

        detected = []
        is_coco = (len(body_keypoints) == 17)
        wrist_indices = [
            (9, "Left", 7),
            (10, "Right", 8)
        ] if is_coco else [
            (4, "Left", 3),   # Roboflow 13 kpt: Wrist Kiri=4, Siku Kiri=3
            (6, "Right", 5)   # Roboflow 13 kpt: Wrist Kanan=6, Siku Kanan=5
        ]

        active = set()
        for w_idx, label, e_idx in wrist_indices:
            if w_idx < len(body_keypoints) and confidences[w_idx] >= 0.20:
                wx, wy = body_keypoints[w_idx]
                if wx == 0 and wy == 0:
                    continue
                active.add(label)

                # Ekstensi 35% panjang lengan ke arah telapak
                if e_idx < len(body_keypoints) and confidences[e_idx] >= 0.20 and not (body_keypoints[e_idx][0] == 0 and body_keypoints[e_idx][1] == 0):
                    ex, ey = body_keypoints[e_idx]
                    dx, dy = float(wx - ex), float(wy - ey)
                    length = max(1e-5, math.hypot(dx, dy))
                    palm_x = float(wx) + (dx / length) * (length * 0.35)
                    palm_y = float(wy) + (dy / length) * (length * 0.35)
                else:
                    palm_x, palm_y = float(wx), float(wy) - 30.0

                palm_pt = np.array([[palm_x, palm_y]], dtype=np.float32)
                if label in self.smoothers:
                    palm_pt = self.smoothers[label].filter(palm_pt, timestamp=timestamp)

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
# 3. STATE ORANG (PERSON STATE PER TRACK_ID)
# ==============================================================================
_PERSON_COLORS = [
    (0, 230, 255),    # Cyan/Kuning Cerah
    (80, 255, 80),    # Hijau Neon
    (0, 140, 255),    # Oranye Cerah
]

class PersonState:
    """Menyimpan seluruh state analisis biomekanik tampak samping untuk 1 orang tertentu."""
    def __init__(self):
        self.smoother = OneEuroFilter(min_cutoff=0.04, beta=0.005)
        self.hand_tracker = PalmCenterTracker()
        self.rep_count = 0
        self.stage = "UP"
        self._depth_buffer = []
        self.depth_pct = 0.0          # 0% saat lengan lurus (UP), 100% saat siku tekuk penuh <=90d (DOWN)
        self.last_seen_time = 0.0
        self.smooth_conf = None
        
        # Side View Profile Locking (Fokus Tampak Samping)
        self.side_conf_ema = {'Left': 0.0, 'Right': 0.0}
        self.active_side = None
        
        # Ground Contact Anchors & Anatomical Bone Constraints
        self.wrist_anchors = {}       # side ('Left'/'Right') -> np.array([x, y]) posisi tumpuan lantai
        self.wrist_corrected = {'Left': False, 'Right': False}
        self.calibrated_arm_len = {}  # side -> panjang lengan atas rata-rata
        
        # Anti-Jitter EMA Angle Smoothing & Persistent Status
        self.exercise = "PUSH_UP"
        self.smooth_elbow_angle = None
        self.smooth_hip_angle = None
        self.smooth_knee_angle = None
        self.last_posture_status = "MENYESUAIKAN POSISI..."
        self.last_posture_color = (0, 255, 255)
        self.elbow_angles_history = []
        self.hip_angles_history = []
        self.last_rep_frame = -999

    def stabilize_and_anchor(self, keypoints, confidences, is_coco=False, enable_ground_anchor=True):
        """
        Ground Contact Anchoring & Anatomical Bone Constraint:
        Mencegah pergelangan tangan (wrist) melayang/melompat saat push-up.
        - Jika deteksi wrist valid dari model (conf >= 0.25), gunakan koordinat asli dan update anchor.
        - Jika deteksi wrist hilang/terhalang (conf < 0.25 / koordinat 0,0), pertahankan di posisi ground anchor.
        """
        kpts = keypoints.copy()
        if not enable_ground_anchor:
            self.wrist_corrected['Left'] = False
            self.wrist_corrected['Right'] = False
            return kpts, self.wrist_corrected

        sh_l, elb_l, wri_l = (5, 7, 9) if is_coco else (1, 3, 4)
        sh_r, elb_r, wri_r = (6, 8, 10) if is_coco else (2, 5, 6)

        arms = [('Left', sh_l, elb_l, wri_l), ('Right', sh_r, elb_r, wri_r)]

        for side, sh, elb, wri in arms:
            if sh >= len(kpts) or elb >= len(kpts) or wri >= len(kpts):
                continue
            
            wri_pt = kpts[wri]
            wri_c = confidences[wri]
            anchor = self.wrist_anchors.get(side)

            # Wrist dianggap tidak valid HANYA jika confidence di bawah batas wajar atau titik hilang (0,0)
            is_invalid_wrist = (wri_c < 0.25) or (wri_pt[0] == 0 and wri_pt[1] == 0)

            if is_invalid_wrist:
                if anchor is not None:
                    # Kunci koordinat wrist ke posisi ground anchor terakhir yang stabil
                    kpts[wri] = anchor.copy()
                    self.wrist_corrected[side] = True
                else:
                    self.wrist_corrected[side] = False
            else:
                # Deteksi valid dari model: perbarui posisi anchor lantai dan nonaktifkan koreksi
                self.wrist_anchors[side] = wri_pt.copy()
                self.wrist_corrected[side] = False

        return kpts, self.wrist_corrected


# ==============================================================================
# 4. BIOMECHANICAL ANALYSIS PIPELINE (VIDEO & REALTIME READY)
# ==============================================================================
class BiomechanicalPipeline:
    def __init__(self, pose_model_path=None, classifier_model_path=None, conf_threshold=0.15, exercise_mode="AUTO"):
        # 1. Konfigurasi Device GPU/CPU
        self.device = 0 if torch.cuda.is_available() else 'cpu'
        device_name = torch.cuda.get_device_name(0) if self.device == 0 else 'CPU'
        print(f"[INFO] Akselerasi Perangkat: {device_name}")

        # 2. Lokasi Model Pose Detector
        if pose_model_path and os.path.exists(pose_model_path):
            target_path = pose_model_path
        else:
            target_path = "yolo11n-pose.pt"

        print(f"[INFO] Loading Model Pose Detector dari: {target_path}")
        self.detector = YOLO(target_path)
        if self.device != 'cpu':
            self.detector.to(self.device)

        self.conf_threshold = conf_threshold
        self.exercise_mode = exercise_mode.upper() if exercise_mode else "AUTO"

        # 3. Load Classifier Eksternal (opsional jika ada .pkl / .joblib)
        self.classifier = None
        if classifier_model_path and os.path.exists(classifier_model_path):
            try:
                import joblib
                self.classifier = joblib.load(classifier_model_path)
                print(f"[INFO] Classifier berhasil dimuat dari: {classifier_model_path}")
            except Exception as e:
                print(f"[WARNING] Gagal memuat classifier: {e}")

        # Inisialisasi state multi-person & Anti-Kedip Coasting
        self.persons = {}          # track_id -> PersonState
        self.primary_person_state = None  # Persistent subject lock untuk push-up (anti-ID-switching)
        self.last_detected_persons = []
        self.last_detected_time = 0.0
        self.COASTING_DURATION_SEC = 0.6
        self.MAX_PERSONS = 1
        self.PERSON_TIMEOUT_SEC = 3.0

        # Ambang batas sudut Push-Up Depth Indicator
        self.PUSHUP_ANGLE_DOWN = 85.0   # Siku tekuk saat turun
        self.PUSHUP_ANGLE_UP = 155.0   # Siku lurus saat posisi atas
        self.frame_idx = 0

    def reset(self):
        """Reset state tracking, deteksi, dan repetisi person untuk pemrosesan video baru."""
        self.persons.clear()
        self.primary_person_state = None
        self.last_detected_persons.clear()
        self.last_detected_time = 0.0
        self.frame_idx = 0

    def classify_exercise(self, kpts, confs):
        """
        Deteksi Jenis Gerakan Otomatis Berdasarkan Geometri Postur Tubuh:
        - SQUAT   : Tubuh vertikal berdiri (Tinggi > Lebar, Bahu di atas Pinggul di atas Kaki).
        - SIT_UP  : Tubuh berbaring terlentang di lantai/matras, lutut menekuk ke atas atau tangan di kepala.
        - PUSH_UP : Tubuh horizontal tengkurap menghadap ke lantai, tangan menapak lantai.
        """
        is_coco = (len(kpts) == 17)
        head_idx = 0
        sh_l, sh_r = (5, 6) if is_coco else (1, 2)
        hip_l, hip_r = (11, 12) if is_coco else (7, 8)
        kne_l, kne_r = (13, 14) if is_coco else (9, 10)
        ank_l, ank_r = (15, 16) if is_coco else (11, 12)
        wri_l, wri_r = (9, 10) if is_coco else (4, 6)

        sh_y = (kpts[sh_l][1] + kpts[sh_r][1]) / 2.0
        sh_x = (kpts[sh_l][0] + kpts[sh_r][0]) / 2.0
        hip_y = (kpts[11][1] + kpts[12][1]) / 2.0
        hip_x = (kpts[11][0] + kpts[12][0]) / 2.0
        kne_y = (kpts[kne_l][1] + kpts[kne_r][1]) / 2.0
        ank_y = (kpts[ank_l][1] + kpts[ank_r][1]) / 2.0
        ank_x = (kpts[ank_l][0] + kpts[ank_r][0]) / 2.0
        wri_y = (kpts[wri_l][1] + kpts[wri_r][1]) / 2.0
        wri_x = (kpts[wri_l][0] + kpts[wri_r][0]) / 2.0
        head_x, head_y = kpts[head_idx][0], kpts[head_idx][1]

        body_height = abs(ank_y - sh_y)
        body_width = abs(ank_x - sh_x)

        # 1. SQUAT: Tubuh tegak vertikal (Bahu di atas Pinggul di atas Kaki)
        if (ank_y - hip_y) > 35 and (hip_y - sh_y) > 25 and body_height > (body_width * 0.85):
            return "SQUAT"

        # 2. SIT-UP vs PUSH-UP:
        # Pada Sit-up: Lutut terangkat di atas pinggul (kne_y < hip_y) atau tangan di kepala dengan lutut tertekuk (kne_y < ank_y)
        torso_len = max(10, np.hypot(sh_x - hip_x, sh_y - hip_y))
        wri_to_head = np.hypot(wri_x - head_x, wri_y - head_y)

        if kne_y < (hip_y - 15):
            return "SIT_UP"
        if wri_to_head < torso_len * 0.65 and kne_y < (ank_y - 15):
            return "SIT_UP"

        return "PUSH_UP"

    def calculate_angle(self, A, B, C):
        """Menghitung sudut 2D pada sendi B menggunakan trigonometri."""
        BA = np.array([A[0] - B[0], A[1] - B[1]], dtype=np.float32)
        BC = np.array([C[0] - B[0], C[1] - B[1]], dtype=np.float32)

        norm_ba = np.linalg.norm(BA)
        norm_bc = np.linalg.norm(BC)
        if norm_ba < 1e-4 or norm_bc < 1e-4:
            return 0.0

        dot_product = np.dot(BA, BC)
        cos_val = np.clip(dot_product / (norm_ba * norm_bc), -1.0, 1.0)
        return float(np.degrees(np.arccos(cos_val)))

    def draw_angle_arc(self, frame, A, B, C, color=(0, 255, 255), radius=28):
        """Menggambar busur derajat visual pada sendi B."""
        try:
            ang_ba = math.degrees(math.atan2(A[1] - B[1], A[0] - B[0]))
            ang_bc = math.degrees(math.atan2(C[1] - B[1], C[0] - B[0]))
            start_ang = int(min(ang_ba, ang_bc))
            end_ang = int(max(ang_ba, ang_bc))
            if (end_ang - start_ang) > 180:
                start_ang, end_ang = end_ang, start_ang + 360
            cv2.ellipse(frame, (int(B[0]), int(B[1])), (radius, radius), 0, start_ang, end_ang, color, 2, cv2.LINE_AA)
        except Exception:
            pass

    def stage1_extract_and_smooth(self, frame, timestamp=None):
        """
        Stage 1: Deteksi pose, multi-person tracking dengan ByteTrack + Fallback Predict,
        dan Confidence-Gated OneEuroFilter smoothing (Anti-Kedip / Zero Flicker).
        """
        if timestamp is None:
            timestamp = time.time()

        try:
            # Gunakan tracking bawaan ultralytics yang tangguh
            results = self.detector.track(
                frame,
                device=self.device,
                conf=self.conf_threshold,
                persist=True,
                verbose=False,
                tracker="bytetrack.yaml"
            )
            # PENTING: ByteTrack bawaan membuang box dengan conf < 0.50 (track_high_thresh).
            # Jika ByteTrack mengembalikan kosong pada frame di mana subjek turun push-up,
            # langsung fallback ke detector.predict() agar titik & kerangka tidak kedip/hilang!
            if (not results or results[0].boxes is None or len(results[0].boxes) == 0
                    or results[0].keypoints is None or len(results[0].keypoints) == 0):
                results = self.detector.predict(
                    frame,
                    device=self.device,
                    conf=self.conf_threshold,
                    verbose=False
                )
        except Exception:
            results = self.detector.predict(
                frame,
                device=self.device,
                conf=self.conf_threshold,
                verbose=False
            )

        if (not results or results[0].keypoints is None or len(results[0].keypoints) == 0
                or results[0].boxes is None or len(results[0].boxes) == 0):
            # Coasting memory: pertahankan pose terakhir hingga 0.6 detik jika ada blur ekstrem 1-2 frame
            if self.last_detected_persons and (timestamp - self.last_detected_time) <= self.COASTING_DURATION_SEC:
                return self.last_detected_persons
            return []

        boxes = results[0].boxes
        confs = boxes.conf.cpu().numpy()
        if boxes.id is not None:
            tids = boxes.id.int().cpu().numpy()
        else:
            tids = np.arange(len(confs), dtype=int)

        cls_ids = boxes.cls.int().cpu().numpy() if boxes.cls is not None else np.zeros(len(confs), dtype=int)

        order = np.argsort(confs)[::-1][:self.MAX_PERSONS]
        detected = []

        for rank, idx in enumerate(order):
            tid = int(tids[idx])
            kpt_data = results[0].keypoints[idx]
            if kpt_data.xy is None or kpt_data.xy.shape[1] == 0:
                continue

            raw_kpts = kpt_data.xy[0].cpu().numpy()
            confidences = (kpt_data.conf[0].cpu().numpy()
                           if kpt_data.conf is not None
                           else np.ones(len(raw_kpts), dtype=np.float32))

            # Anti-Jitter: Kunci subjek utama agar riwayat filter tidak di-reset saat ByteTrack putus ID
            if rank == 0:
                if self.primary_person_state is None:
                    self.primary_person_state = PersonState()
                pstate = self.primary_person_state
                self.persons[tid] = pstate
            else:
                if tid not in self.persons:
                    self.persons[tid] = PersonState()
                pstate = self.persons[tid]

            pstate.last_seen_time = timestamp

            # Smoothing koordinat keypoint dengan Confidence-Gated OneEuroFilter
            smoothed_kpts = pstate.smoother.filter(raw_kpts, conf=confidences, timestamp=timestamp, min_conf=0.15)

            # Smoothing & Persistence Confidence (agar titik yang di-hold oleh OneEuroFilter tetap digambar tanpa kedip)
            valid_mask = (confidences >= 0.15) & ~((raw_kpts[:, 0] == 0) & (raw_kpts[:, 1] == 0))
            boosted_conf = np.where(valid_mask, np.maximum(confidences, 0.65), 0.0)
            if pstate.smooth_conf is None or pstate.smooth_conf.shape != confidences.shape:
                pstate.smooth_conf = boosted_conf.astype(np.float32)
            else:
                pstate.smooth_conf = np.where(
                    valid_mask,
                    np.maximum(boosted_conf, 0.7 * pstate.smooth_conf + 0.3 * boosted_conf),
                    pstate.smooth_conf * 0.92  # Decay lembut saat sendi tertutup sesaat
                ).astype(np.float32)

            # Deteksi nama gerakan & jenis exercise (Auto-Classify jika AUTO)
            if self.exercise_mode == "AUTO":
                detected_ex = self.classify_exercise(raw_kpts, confidences)
                if not hasattr(pstate, '_ex_votes'):
                    pstate._ex_votes = {}
                pstate._ex_votes[detected_ex] = pstate._ex_votes.get(detected_ex, 0) + 1
                if sum(pstate._ex_votes.values()) >= 5:
                    pstate.exercise = max(pstate._ex_votes, key=pstate._ex_votes.get)
                else:
                    pstate.exercise = detected_ex
            else:
                pstate.exercise = self.exercise_mode

            movement = pstate.exercise
            is_pushup = (pstate.exercise == "PUSH_UP")

            # Stabilisasi kerangka lengan & pergelangan tangan (Ground Contact Anchor HANYA untuk push-up)
            stabilized_kpts, _ = pstate.stabilize_and_anchor(
                smoothed_kpts, pstate.smooth_conf, is_coco=(len(smoothed_kpts) == 17),
                enable_ground_anchor=is_pushup
            )

            detected.append({
                'track_id': tid,
                'rank': rank,
                'keypoints': stabilized_kpts,
                'confidences': pstate.smooth_conf,
                'movement': movement
            })

        # Hapus state orang yang sudah hilang > PERSON_TIMEOUT_SEC
        stale_tids = [tid for tid, ps in self.persons.items() if (timestamp - ps.last_seen_time) > self.PERSON_TIMEOUT_SEC]
        for tid in stale_tids:
            del self.persons[tid]

        if detected:
            self.last_detected_persons = detected
            self.last_detected_time = timestamp

        return detected

    def stage3_visualize_and_evaluate(self, movement, keypoints, confidences, hands_data, frame,
                                       pstate, person_rank=0, fps_display=0.0):
        """
        Stage 3: Evaluasi Biomekanik Berbasis Sudut (Angle-Primary) & Tampak Samping (Side-View Only).
        Fokus hanya pada 1 sisi tampak samping yang menghadap kamera dan menyederhanakan visualisasi
        agar kerangka skeleton bersih, presisi, dan tidak pecah.
        """
        h, w = frame.shape[:2]
        p_color = _PERSON_COLORS[min(person_rank, len(_PERSON_COLORS) - 1)]

        # Definisi Indeks Keypoint per Sisi (Roboflow 13 vs COCO 17)
        if len(keypoints) == 13:
            head_idx = 0
            sh_l, elb_l, wri_l = 1, 3, 4
            sh_r, elb_r, wri_r = 2, 5, 6
            hip_l, kne_l, ank_l = 7, 9, 11
            hip_r, kne_r, ank_r = 8, 10, 12
        else:
            head_idx = 0
            sh_l, elb_l, wri_l = 5, 7, 9
            sh_r, elb_r, wri_r = 6, 8, 10
            hip_l, kne_l, ank_l = 11, 13, 15
            hip_r, kne_r, ank_r = 12, 14, 16

        def is_valid_pt(idx, min_conf=0.20):
            if idx >= len(keypoints) or confidences[idx] < min_conf:
                return False
            x, y = keypoints[idx][0], keypoints[idx][1]
            if x == 0 and y == 0:
                return False
            return True

        # ── 1. Side-View Profile Selection (Deteksi Sisi Menghadap Kamera) ───
        head_x = keypoints[head_idx][0]
        hip_center_x = (keypoints[hip_l][0] + keypoints[hip_r][0]) / 2.0

        conf_l = (confidences[sh_l] + confidences[elb_l] + confidences[wri_l] + confidences[hip_l]) / 4.0
        conf_r = (confidences[sh_r] + confidences[elb_r] + confidences[wri_r] + confidences[hip_r]) / 4.0

        pstate.side_conf_ema['Left'] = 0.90 * pstate.side_conf_ema['Left'] + 0.10 * conf_l
        pstate.side_conf_ema['Right'] = 0.90 * pstate.side_conf_ema['Right'] + 0.10 * conf_r

        # Pada posisi push-up horizontal:
        # Jika kepala di kanan (head_x > hip_x): sisi kanan (Right) menghadap ke kamera
        # Jika kepala di kiri (head_x < hip_x): sisi kiri (Left) menghadap ke kamera
        if is_valid_pt(head_idx) and is_valid_pt(hip_l) and is_valid_pt(hip_r):
            if head_x > (hip_center_x + 20):
                target_side = 'Right'
            elif head_x < (hip_center_x - 20):
                target_side = 'Left'
            else:
                target_side = 'Right' if pstate.side_conf_ema['Right'] >= pstate.side_conf_ema['Left'] else 'Left'
        else:
            target_side = 'Right' if pstate.side_conf_ema['Right'] >= pstate.side_conf_ema['Left'] else 'Left'

        if pstate.active_side is None:
            pstate.active_side = target_side
        elif pstate.active_side != target_side:
            if not hasattr(pstate, '_side_switch_cnt'):
                pstate._side_switch_cnt = 0
            pstate._side_switch_cnt += 1
            if pstate._side_switch_cnt >= 8:
                pstate.active_side = target_side
                pstate._side_switch_cnt = 0
        else:
            pstate._side_switch_cnt = 0

        cur_side = pstate.active_side
        bg_side = 'Left' if cur_side == 'Right' else 'Right'
        profil_txt = "KANAN" if cur_side == "Right" else "KIRI"

        if cur_side == 'Left':
            cur_sh, cur_elb, cur_wri = sh_l, elb_l, wri_l
            cur_hip, cur_kne, cur_ank = hip_l, kne_l, ank_l
            bg_sh, bg_elb, bg_wri = sh_r, elb_r, wri_r
            bg_hip, bg_kne, bg_ank = hip_r, kne_r, ank_r
        else:
            cur_sh, cur_elb, cur_wri = sh_r, elb_r, wri_r
            cur_hip, cur_kne, cur_ank = hip_r, kne_r, ank_r
            bg_sh, bg_elb, bg_wri = sh_l, elb_l, wri_l
            bg_hip, bg_kne, bg_ank = hip_l, kne_l, ank_l

        # ── 2. Gambar Kerangka Skeleton Utuh (Warna Seragam / Uniform p_color) ─
        # Seluruh ruas tulang digambar tersambung kokoh (anti-patah / anti-melayang)
        all_limbs = [
            # Kaki Kiri & Kanan
            (hip_l, kne_l), (kne_l, ank_l),
            (hip_r, kne_r), (kne_r, ank_r),
            # Badan & Torso
            (sh_l, sh_r), (hip_l, hip_r),
            (sh_l, hip_l), (sh_r, hip_r)
        ]

        # Lengan Kanan: Cegah lengan melayang terputus tanpa bahu
        if is_valid_pt(sh_r) and is_valid_pt(elb_r):
            all_limbs.append((sh_r, elb_r))
            if is_valid_pt(wri_r):
                all_limbs.append((elb_r, wri_r))
        elif is_valid_pt(elb_r) and is_valid_pt(wri_r) and is_valid_pt(sh_l):
            # Sambungkan ke bahu kiri jika bahu kanan tepat di luar frame
            all_limbs.append((sh_l, elb_r))
            all_limbs.append((elb_r, wri_r))

        # Lengan Kiri: Cegah lengan melayang terputus tanpa bahu
        if is_valid_pt(sh_l) and is_valid_pt(elb_l):
            all_limbs.append((sh_l, elb_l))
            if is_valid_pt(wri_l):
                all_limbs.append((elb_l, wri_l))
        elif is_valid_pt(elb_l) and is_valid_pt(wri_l) and is_valid_pt(sh_r):
            all_limbs.append((sh_r, elb_l))
            all_limbs.append((elb_l, wri_l))

        for p1, p2 in all_limbs:
            if is_valid_pt(p1) and is_valid_pt(p2):
                x1 = int(np.clip(keypoints[p1][0], 0, w - 1))
                y1 = int(np.clip(keypoints[p1][1], 0, h - 1))
                x2 = int(np.clip(keypoints[p2][0], 0, w - 1))
                y2 = int(np.clip(keypoints[p2][1], 0, h - 1))
                cv2.line(frame, (x1, y1), (x2, y2), p_color, 3, cv2.LINE_AA)

        # Validasi Visibilitas Kepala: Cegah skeleton aneh/menembak ke langit-langit saat kepala terpotong di luar frame
        head_visible = False
        if is_valid_pt(head_idx, min_conf=0.35):
            hx, hy = keypoints[head_idx][0], keypoints[head_idx][1]
            head_margin = 25
            # Cek apakah koordinat kepala berada di dalam area aman frame (bukan di tepi terpotong)
            if (head_margin <= hx <= w - head_margin) and (head_margin <= hy <= h - head_margin):
                if is_valid_pt(sh_l) and is_valid_pt(sh_r):
                    neck_y = (keypoints[sh_l][1] + keypoints[sh_r][1]) / 2.0
                    # Pada posisi squat: jika kepala berada sejajar/di bawah bahu, berarti terpotong
                    if pstate.exercise == "SQUAT" and hy >= (neck_y - 6.0):
                        head_visible = False
                    else:
                        head_visible = True
                else:
                    head_visible = True

        # Garis Leher ke Kepala Natural (HANYA jika kepala benar-benar terlihat di dalam frame)
        if head_visible and is_valid_pt(sh_l) and is_valid_pt(sh_r):
            neck_pt = (int((keypoints[sh_l][0] + keypoints[sh_r][0]) / 2),
                       int((keypoints[sh_l][1] + keypoints[sh_r][1]) / 2))
            head_pt = (int(keypoints[head_idx][0]), int(keypoints[head_idx][1]))
            cv2.line(frame, neck_pt, head_pt, p_color, 3, cv2.LINE_AA)

        # Seluruh Titik Sendi Tubuh dengan Style & Warna Seragam
        all_joints = [sh_l, elb_l, wri_l, sh_r, elb_r, wri_r,
                      hip_l, kne_l, ank_l, hip_r, kne_r, ank_r]
        if head_visible:
            all_joints.insert(0, head_idx)
        for i in all_joints:
            if is_valid_pt(i):
                kx = int(np.clip(keypoints[i][0], 0, w - 1))
                ky = int(np.clip(keypoints[i][1], 0, h - 1))
                wrist_side = 'Left' if i == wri_l else ('Right' if i == wri_r else None)
                is_pushup = (pstate.exercise == "PUSH_UP")
                is_anchored = is_pushup and (wrist_side is not None) and pstate.wrist_corrected.get(wrist_side, False)
                joint_color = (0, 165, 255) if is_anchored else (255, 255, 255)

                cv2.circle(frame, (kx, ky), 6, p_color, -1, cv2.LINE_AA)
                cv2.circle(frame, (kx, ky), 4, joint_color, -1, cv2.LINE_AA)

                if is_anchored and i == cur_wri:
                    cv2.putText(frame, "[A]", (kx + 8, ky - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 165, 255), 1, cv2.LINE_AA)

        # ── 4. Evaluasi Biomekanik & Repetisi Sesuai Jenis Gerakan ──────────
        hip_angle = pstate.smooth_hip_angle if pstate.smooth_hip_angle is not None else 0.0
        elbow_angle = pstate.smooth_elbow_angle if pstate.smooth_elbow_angle is not None else 0.0
        knee_angle = pstate.smooth_knee_angle if pstate.smooth_knee_angle is not None else 0.0
        posture_status = pstate.last_posture_status
        posture_color = pstate.last_posture_color

        current_ex = pstate.exercise  # "SQUAT", "SIT_UP", atau "PUSH_UP"

        if current_ex == "SQUAT":
            # ======================== SQUAT BIOMECHANICS ========================
            # Sudut Utama: Sudut Lutut (Pinggul - Lutut - Pergelangan Kaki)
            if is_valid_pt(cur_hip, 0.20) and is_valid_pt(cur_kne, 0.20) and is_valid_pt(cur_ank, 0.20):
                raw_knee = self.calculate_angle(keypoints[cur_hip], keypoints[cur_kne], keypoints[cur_ank])
                pstate.smooth_knee_angle = raw_knee if pstate.smooth_knee_angle is None else (0.70 * pstate.smooth_knee_angle + 0.30 * raw_knee)
                knee_angle = pstate.smooth_knee_angle

                # Busur Lutut (Knee Arc)
                arc_col = (0, 255, 0) if knee_angle <= 100.0 else ((0, 230, 255) if knee_angle <= 140.0 else (255, 0, 255))
                self.draw_angle_arc(frame, keypoints[cur_hip], keypoints[cur_kne], keypoints[cur_ank], color=arc_col, radius=28)
                kne_pt = (int(keypoints[cur_kne][0]), int(keypoints[cur_kne][1]))
                kne_txt = f"{int(knee_angle)} deg"
                cv2.putText(frame, kne_txt, (kne_pt[0] + 36, kne_pt[1] + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 0, 0), 3, cv2.LINE_AA)
                cv2.putText(frame, kne_txt, (kne_pt[0] + 36, kne_pt[1] + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.58, arc_col, 2, cv2.LINE_AA)

                # State Machine Squat: DOWN saat lutut <= 100d, UP saat lutut >= 150d (+1 rep)
                if knee_angle <= 100.0 and pstate.stage == "UP":
                    pstate.stage = "DOWN"
                elif knee_angle >= 150.0 and pstate.stage == "DOWN":
                    pstate.stage = "UP"
                    pstate.rep_count += 1

            # Sudut Sekunder: Kelurusan Punggung (Bahu - Pinggul - Lutut)
            if is_valid_pt(cur_sh, 0.20) and is_valid_pt(cur_hip, 0.20) and is_valid_pt(cur_kne, 0.20):
                raw_hip = self.calculate_angle(keypoints[cur_sh], keypoints[cur_hip], keypoints[cur_kne])
                pstate.smooth_hip_angle = raw_hip if pstate.smooth_hip_angle is None else (0.75 * pstate.smooth_hip_angle + 0.25 * raw_hip)
                hip_angle = pstate.smooth_hip_angle
                self.draw_angle_arc(frame, keypoints[cur_sh], keypoints[cur_hip], keypoints[cur_kne], color=(0, 255, 255), radius=30)
                hip_pt = (int(keypoints[cur_hip][0]), int(keypoints[cur_hip][1]))
                hip_txt = f"{int(hip_angle)} deg"
                cv2.putText(frame, hip_txt, (hip_pt[0] + 36, hip_pt[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 0, 0), 3, cv2.LINE_AA)
                cv2.putText(frame, hip_txt, (hip_pt[0] + 36, hip_pt[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 255, 255), 2, cv2.LINE_AA)

                posture_status = "PUNGGUNG BAIK" if hip_angle >= 70.0 else "TERLALU BUNGKUK"
                posture_color = (0, 255, 0) if hip_angle >= 70.0 else (0, 0, 255)

            title_str = f"SQUAT • PROFIL {profil_txt}"
            line3_str = f"Lutut: {int(knee_angle)}d | Pinggul: {int(hip_angle)}d"

        elif current_ex == "SIT_UP":
            # ======================== SIT-UP BIOMECHANICS =======================
            # Sudut Utama: Fleksi Torso/Pinggul (Bahu - Pinggul - Lutut)
            if is_valid_pt(cur_sh, 0.20) and is_valid_pt(cur_hip, 0.20) and is_valid_pt(cur_kne, 0.20):
                raw_hip = self.calculate_angle(keypoints[cur_sh], keypoints[cur_hip], keypoints[cur_kne])
                pstate.smooth_hip_angle = raw_hip if pstate.smooth_hip_angle is None else (0.70 * pstate.smooth_hip_angle + 0.30 * raw_hip)
                hip_angle = pstate.smooth_hip_angle

                # Busur Pinggul (Hip Flexion Arc)
                arc_col = (0, 255, 0) if hip_angle <= 95.0 else ((0, 230, 255) if hip_angle <= 125.0 else (255, 0, 255))
                self.draw_angle_arc(frame, keypoints[cur_sh], keypoints[cur_hip], keypoints[cur_kne], color=arc_col, radius=30)
                hip_pt = (int(keypoints[cur_hip][0]), int(keypoints[cur_hip][1]))
                hip_txt = f"{int(hip_angle)} deg"
                cv2.putText(frame, hip_txt, (hip_pt[0] + 36, hip_pt[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 0, 0), 3, cv2.LINE_AA)
                cv2.putText(frame, hip_txt, (hip_pt[0] + 36, hip_pt[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.58, arc_col, 2, cv2.LINE_AA)

                # State Machine Sit-up:
                # 1. Posisi awal/relaksasi: Rebahan di matras (DOWN: hip >= 104 deg)
                # 2. Posisi puncak kontraksi: Mengangkat torso ke atas (UP: hip <= 88 deg -> Repetisi +1)
                # 3. Transisi kembali ke matras: Rebah kembali (DOWN: hip >= 104 deg)
                if pstate.stage not in ("UP", "DOWN"):
                    pstate.stage = "DOWN" if hip_angle >= 100.0 else "UP"

                # Otomatis reset ke DOWN jika atlet di awal video sedang rebahan (hip >= 104 deg)
                if pstate.rep_count == 0 and pstate.stage == "UP" and hip_angle >= 104.0:
                    pstate.stage = "DOWN"

                # Hitung Repetisi saat atlet sukses mengangkat torso ke atas (puncak kontraksi UP)
                if hip_angle <= 88.0 and pstate.stage == "DOWN":
                    pstate.stage = "UP"
                    pstate.rep_count += 1
                # Kembalikan state ke DOWN saat atlet rebah kembali ke matras
                elif hip_angle >= 104.0 and pstate.stage == "UP":
                    pstate.stage = "DOWN"

                posture_status = "KONTRAKSI PERUT" if hip_angle <= 88.0 else ("PERSIAPAN NAIK" if hip_angle <= 100.0 else "REBAH / MATRAS")
                posture_color = (0, 255, 0) if hip_angle <= 88.0 else ((0, 255, 255) if hip_angle <= 100.0 else (200, 200, 200))

            # Sudut Lutut (Tekukan Kaki)
            if is_valid_pt(cur_hip, 0.20) and is_valid_pt(cur_kne, 0.20) and is_valid_pt(cur_ank, 0.20):
                raw_knee = self.calculate_angle(keypoints[cur_hip], keypoints[cur_kne], keypoints[cur_ank])
                pstate.smooth_knee_angle = raw_knee if pstate.smooth_knee_angle is None else (0.75 * pstate.smooth_knee_angle + 0.25 * raw_knee)
                knee_angle = pstate.smooth_knee_angle

            title_str = f"SIT-UP • PROFIL {profil_txt}"
            line3_str = f"Torso: {int(hip_angle)}d | Lutut: {int(knee_angle)}d"

        else:
            # ======================= PUSH-UP BIOMECHANICS =======================
            # Evaluasi Pinggul Plank
            ref_leg = cur_ank if is_valid_pt(cur_ank, 0.20) else (cur_kne if is_valid_pt(cur_kne, 0.20) else None)
            if is_valid_pt(cur_sh, 0.20) and is_valid_pt(cur_hip, 0.20) and ref_leg is not None:
                raw_hip = self.calculate_angle(keypoints[cur_sh], keypoints[cur_hip], keypoints[ref_leg])
                pstate.smooth_hip_angle = raw_hip if pstate.smooth_hip_angle is None else (0.75 * pstate.smooth_hip_angle + 0.25 * raw_hip)
                hip_angle = pstate.smooth_hip_angle
                self.draw_angle_arc(frame, keypoints[cur_sh], keypoints[cur_hip], keypoints[ref_leg], color=(0, 255, 255), radius=30)
                hip_pt = (int(keypoints[cur_hip][0]), int(keypoints[cur_hip][1]))
                hip_txt = f"{int(hip_angle)} deg"
                cv2.putText(frame, hip_txt, (hip_pt[0] + 36, hip_pt[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 0, 0), 3, cv2.LINE_AA)
                cv2.putText(frame, hip_txt, (hip_pt[0] + 36, hip_pt[1] - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 255, 255), 2, cv2.LINE_AA)
                posture_status = "POSTUR SEMPURNA" if hip_angle >= 160 else ("POSTUR BAIK" if hip_angle >= 140 else "PINGGUL TURUN / MELENGKUNG")
                posture_color = (0, 255, 0) if hip_angle >= 160 else ((0, 255, 255) if hip_angle >= 140 else (0, 0, 255))

            # Evaluasi Siku Push-Up
            if is_valid_pt(cur_sh, 0.20) and is_valid_pt(cur_elb, 0.20) and is_valid_pt(cur_wri, 0.20):
                raw_elbow = self.calculate_angle(keypoints[cur_sh], keypoints[cur_elb], keypoints[cur_wri])
                pstate.smooth_elbow_angle = raw_elbow if pstate.smooth_elbow_angle is None else (0.60 * pstate.smooth_elbow_angle + 0.40 * raw_elbow)
                elbow_angle = pstate.smooth_elbow_angle

                arc_col = (0, 255, 0) if elbow_angle <= 90.0 else ((0, 230, 255) if elbow_angle <= 125.0 else (255, 0, 255))
                self.draw_angle_arc(frame, keypoints[cur_sh], keypoints[cur_elb], keypoints[cur_wri], color=arc_col, radius=28)
                elb_pt = (int(keypoints[cur_elb][0]), int(keypoints[cur_elb][1]))
                elb_txt = f"{int(elbow_angle)} deg"
                cv2.putText(frame, elb_txt, (elb_pt[0] + 36, elb_pt[1] + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 0, 0), 3, cv2.LINE_AA)
                cv2.putText(frame, elb_txt, (elb_pt[0] + 36, elb_pt[1] + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.58, arc_col, 2, cv2.LINE_AA)

                # Evaluasi lengan latar belakang (bg_side) untuk menangani sudut kamera oblique / elbow flare
                bg_elbow_conf = min(confidences[bg_sh], confidences[bg_elb], confidences[bg_wri]) if (bg_sh < len(confidences) and bg_elb < len(confidences) and bg_wri < len(confidences)) else 0.0
                raw_bg_elbow = None
                if is_valid_pt(bg_sh, 0.20) and is_valid_pt(bg_elb, 0.20) and is_valid_pt(bg_wri, 0.20) and bg_elbow_conf >= 0.35:
                    raw_bg_elbow = self.calculate_angle(keypoints[bg_sh], keypoints[bg_elb], keypoints[bg_wri])

                # State Machine Push-Up (Dual-Arm Aware & Anti-Noise Debounce):
                # - DOWN: Siku menekuk ke bawah (smooth <= 103.0 deg atau raw <= 103.0 deg,
                #         atau jika lengan latar tekuk <= 103.0 deg saat lengan aktif sudah turun <= 118.0 deg)
                # - UP: Lengan dorong lurus ke atas (smooth >= 126.0 deg atau raw >= 128.0 deg -> Repetisi +1)
                bg_down = (raw_bg_elbow is not None and raw_bg_elbow <= 103.0 and elbow_angle <= 118.0)
                is_push_down = (elbow_angle <= 103.0 or raw_elbow <= 103.0 or bg_down)
                is_push_up = (elbow_angle >= 126.0 or raw_elbow >= 128.0)

                current_f = getattr(self, 'frame_idx', 0)
                if is_push_down and pstate.stage == "UP":
                    pstate.stage = "DOWN"
                elif is_push_up and pstate.stage == "DOWN":
                    if not hasattr(pstate, 'last_rep_frame'):
                        pstate.last_rep_frame = -999
                    if (current_f - pstate.last_rep_frame) >= 12:  # Debounce refractory period (~0.4s)
                        pstate.stage = "UP"
                        pstate.rep_count += 1
                        pstate.last_rep_frame = current_f

            title_str = f"PUSH-UP • PROFIL {profil_txt}"
            line3_str = f"Siku: {int(elbow_angle)}d | Pinggul: {int(hip_angle)}d"

        pstate.last_posture_status = posture_status
        pstate.last_posture_color = posture_color

        # ── 5. Compact HUD Dashboard Card (Ramping & Elegan) ─────────────────
        hud_w, hud_h = 210, 86
        hud_x = max(10, w - hud_w - 15)
        hud_y = 15

        overlay = frame.copy()
        cv2.rectangle(overlay, (hud_x, hud_y), (hud_x + hud_w, hud_y + hud_h), (18, 18, 22), -1)
        cv2.addWeighted(overlay, 0.78, frame, 0.22, 0, frame)
        cv2.rectangle(frame, (hud_x, hud_y), (hud_x + hud_w, hud_y + hud_h), p_color, 1)

        cv2.putText(frame, title_str, (hud_x + 8, hud_y + 18),
                    cv2.FONT_HERSHEY_DUPLEX, 0.35, p_color, 1, cv2.LINE_AA)

        cv2.putText(frame, f"REPS: {pstate.rep_count}", (hud_x + 8, hud_y + 40),
                    cv2.FONT_HERSHEY_DUPLEX, 0.60, (0, 255, 0), 1, cv2.LINE_AA)
        stage_color = (0, 230, 255) if pstate.stage == "DOWN" else (255, 255, 255)
        cv2.putText(frame, f"[{pstate.stage}]", (hud_x + 130, hud_y + 40),
                    cv2.FONT_HERSHEY_DUPLEX, 0.50, stage_color, 1, cv2.LINE_AA)

        elbow_color = (0, 255, 0) if (elbow_angle <= 95.0 or knee_angle <= 100.0 or (current_ex == "SIT_UP" and hip_angle <= 95.0)) else (220, 220, 220)
        cv2.putText(frame, line3_str, (hud_x + 8, hud_y + 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.33, elbow_color, 1, cv2.LINE_AA)

        cv2.putText(frame, f"Postur: {posture_status[:20]}", (hud_x + 8, hud_y + 77),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.33, posture_color, 1, cv2.LINE_AA)

        return frame

    def process_frame(self, frame, timestamp=None, fps_display=0.0):
        """Pipeline utama pemrosesan frame."""
        self.frame_idx += 1
        detected_persons = self.stage1_extract_and_smooth(frame, timestamp)

        for person in detected_persons:
            tid = person['track_id']
            rank = person['rank']
            kpts = person['keypoints']
            conf = person['confidences']
            movement = person['movement']

            pstate = self.persons[tid]
            hands_data = pstate.hand_tracker.extract_hands(kpts, conf, timestamp)

            frame = self.stage3_visualize_and_evaluate(
                movement, kpts, conf, hands_data, frame,
                pstate, person_rank=rank, fps_display=fps_display
            )

        return frame


# ==============================================================================
# 5. PEMROSESAN VIDEO & ENTRY POINT (BATCH FOLDER / SINGLE VIDEO)
# ==============================================================================
def process_single_video(input_video_path, output_dir, pipeline, video_idx=1, total_videos=1):
    """Memproses satu file video, menganalisis pose & repetisi, lalu menyimpan hasil konversi."""
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print(f"[ERROR] Gagal membuka video: {input_video_path}")
        return None

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(input_video_path))[0]
    output_video_path = os.path.join(output_dir, f"{base_name}_biomekanik_eval.mp4")

    print("\n" + "=" * 75)
    print(f"  [VIDEO {video_idx}/{total_videos}] MEMPROSES: {os.path.basename(input_video_path)}")
    print("=" * 75)
    print(f" Input Video   : {input_video_path}")
    print(f" Output Video  : {output_video_path}")
    print(f" Resolusi      : {width}x{height} @ {fps:.1f} FPS (Total: {total_frames} frame)")

    # Inisialisasi VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    if not out.isOpened():
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        output_video_path = output_video_path.replace('.mp4', '.avi')
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    # Reset state pelacakan dan repetisi untuk video baru
    pipeline.reset()

    t_start = time.time()
    processed_count = 0
    recent_fps = fps

    desc = f"[{video_idx}/{total_videos}] {os.path.basename(input_video_path)[:22]}"
    pbar = tqdm(range(total_frames), desc=desc, total=total_frames)
    for frame_idx in pbar:
        ret, frame = cap.read()
        if not ret or frame is None:
            break

        timestamp = frame_idx / max(1.0, fps)

        t_f0 = time.time()
        annotated_frame = pipeline.process_frame(frame, timestamp=timestamp, fps_display=recent_fps)
        t_f1 = time.time()

        frame_duration = max(1e-4, t_f1 - t_f0)
        recent_fps = 0.9 * recent_fps + 0.1 * (1.0 / frame_duration)

        out.write(annotated_frame)
        processed_count += 1

    cap.release()
    out.release()
    total_time = time.time() - t_start
    avg_speed = (processed_count / total_time) if total_time > 0 else 0

    reps_detected = 0
    exercise_name = "UNKNOWN"
    if pipeline.primary_person_state:
        reps_detected = pipeline.primary_person_state.rep_count
        exercise_name = pipeline.primary_person_state.exercise
    elif pipeline.persons:
        best_p = max(pipeline.persons.values(), key=lambda p: p.rep_count)
        reps_detected = best_p.rep_count
        exercise_name = best_p.exercise

    print(f"  -> Selesai! Frame: {processed_count}/{total_frames} | Waktu: {total_time:.1f}s ({avg_speed:.1f} FPS) | Gerakan: {exercise_name} | Repetisi: {reps_detected}")

    return {
        'video_name': os.path.basename(input_video_path),
        'exercise': exercise_name,
        'frames': processed_count,
        'reps': reps_detected,
        'duration_s': processed_count / max(1.0, fps),
        'proc_time_s': total_time,
        'fps_proc': avg_speed,
        'output_path': output_video_path
    }


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.abspath(os.path.join(script_dir, '..'))

    # ==========================================================================
    # PILIHAN MODEL DETEKSI POSE (.pt):
    # - Ubah variabel GUNAKAN_CUSTOM_MODEL ke True untuk model training kamu (best.pt)
    # - Ubah ke False jika ingin menggunakan model bawaan COCO (yolo11n-pose.pt)
    # ==========================================================================
    GUNAKAN_CUSTOM_MODEL = True

    if GUNAKAN_CUSTOM_MODEL:
        custom_candidates = [
            os.path.join(workspace_root, 'data Best PT', 'best.pt'),
            os.path.join(script_dir, 'runs', 'pose_models', 'yolo11s-pose', 'weights', 'best.pt'),
            os.path.join(script_dir, 'runs', 'pose_models', 'yolo11n-pose', 'weights', 'best.pt'),
            os.path.join(workspace_root, 'data Best PT', 'bestt.pt'),
            os.path.join(script_dir, 'best.pt')
        ]
        model_path = next((p for p in custom_candidates if os.path.exists(p)), None)
        if not model_path:
            print("[WARNING] Model custom best.pt tidak ditemukan, beralih ke yolo11n-pose.pt")
            model_path = os.path.join(script_dir, "yolo11n-pose.pt")
    else:
        model_path = os.path.join(script_dir, "yolo11n-pose.pt")
        if not os.path.exists(model_path):
            model_path = "yolo11n-pose.pt"

    # ==========================================================================
    # INPUT VIDEO & MODE OLAHRAGA (FITNESS EXERCISE):
    # - VIDEO_INPUT    : Path file video tunggal ATAU nama/path folder kumpulan video
    #                    Contoh folder: "push up 10 video"
    #                    Contoh file  : "push-up_19.mp4", "push up 2.mp4"
    # - OUTPUT_FOLDER  : Nama folder tujuan hasil konversi (misal: "push up hasil konversi")
    # - EXERCISE_MODE  : "AUTO" (otomatis deteksi gerakan), "PUSH_UP", "SQUAT", atau "SIT_UP"
    # ==========================================================================
    VIDEO_INPUT = "push up kurang bagus"
    OUTPUT_FOLDER = "push up kurang bagus"
    EXERCISE_MODE = "AUTO"

    # Pencarian target input (bisa berupa folder atau file video)
    candidates = [
        VIDEO_INPUT,
        os.path.join(workspace_root, VIDEO_INPUT),
        os.path.join(workspace_root, 'Tumbal ekstrak', VIDEO_INPUT),
        os.path.join(workspace_root, 'Tumbal ekstrak', f"video {VIDEO_INPUT}"),
        os.path.join(workspace_root, 'Tumbal ekstrak', VIDEO_INPUT.replace('video ', '')),
        os.path.join(script_dir, VIDEO_INPUT)
    ]
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        target_input = sys.argv[1]
    else:
        target_input = next((p for p in candidates if os.path.exists(p)), None)

    # Validasi keberadaan target input
    if not target_input:
        print("\n" + "=" * 75)
        print(f" [ERROR] File atau folder input TIDAK ditemukan: {VIDEO_INPUT}")
        print(f" [PETUNJUK] Pastikan '{VIDEO_INPUT}' ada di folder dataset atau 'Tumbal ekstrak'.")
        print("=" * 75 + "\n")
        return

    # Deteksi apakah target adalah Folder atau File Tunggal
    is_batch_dir = os.path.isdir(target_input)
    valid_exts = ('.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v')

    if is_batch_dir:
        video_files = [
            os.path.join(target_input, f)
            for f in os.listdir(target_input)
            if os.path.isfile(os.path.join(target_input, f)) and f.lower().endswith(valid_exts)
        ]
        video_files.sort()
        if not video_files:
            print(f"[ERROR] Tidak ditemukan file video {valid_exts} di folder: {target_input}")
            return
    else:
        video_files = [target_input]

    # Tentukan Direktori Output
    if OUTPUT_FOLDER:
        output_dir = os.path.join(workspace_root, OUTPUT_FOLDER) if not os.path.isabs(OUTPUT_FOLDER) else OUTPUT_FOLDER
    else:
        output_dir = os.path.join(workspace_root, 'push up hasil konversi' if is_batch_dir else 'hasil Video Konversi')
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 75)
    print("  [BIOMECHANICAL PIPELINE] ANALISIS VIDEO POSE, REPS & BIOMEKANIK")
    print("=" * 75)
    print(f" Mode Input    : {'BATCH FOLDER' if is_batch_dir else 'SINGLE VIDEO'}")
    print(f" Lokasi Input  : {target_input}")
    print(f" Jumlah Video  : {len(video_files)} file")
    print(f" Folder Output : {output_dir}")
    print(f" Model Path    : {model_path}")
    print(f" Exercise Mode : {EXERCISE_MODE}")
    print("=" * 75)

    # Inisialisasi Pipeline Sekali Saja (Model dimuat 1x ke memori untuk efisiensi CPU/GPU)
    pipeline = BiomechanicalPipeline(pose_model_path=model_path, conf_threshold=0.15, exercise_mode=EXERCISE_MODE)

    # Eksekusi Setiap Video
    results_summary = []
    total_start_time = time.time()

    for idx, vid_path in enumerate(video_files, 1):
        res = process_single_video(
            input_video_path=vid_path,
            output_dir=output_dir,
            pipeline=pipeline,
            video_idx=idx,
            total_videos=len(video_files)
        )
        if res:
            results_summary.append(res)

    grand_total_time = time.time() - total_start_time

    # Tampilkan Tabel Ringkasan Hasil
    print("\n" + "=" * 80)
    print("  [RINGKASAN HASIL KONVERSI VIDEO BIOMEKANIK]")
    print("=" * 80)
    print(f"{'No':<3} | {'Nama Video':<24} | {'Gerakan':<10} | {'Frame':<7} | {'Durasi':<8} | {'Repetisi':<9} | {'Speed':<9}")
    print("-" * 80)
    total_reps_all = 0
    total_frames_all = 0
    for i, res in enumerate(results_summary, 1):
        total_reps_all += res['reps']
        total_frames_all += res['frames']
        print(f"{i:<3} | {res['video_name']:<24} | {res['exercise']:<10} | {res['frames']:<7} | {res['duration_s']:>6.1f}s  | {res['reps']:>8}  | {res['fps_proc']:>5.1f} FPS")
    print("-" * 80)
    print(f"TOTAL: {len(results_summary)} Video | {total_frames_all} Frame | {total_reps_all} Repetisi | Total Waktu: {grand_total_time:.1f}s")
    print("=" * 80)
    print(f" Seluruh video hasil evaluasi tersimpan di folder:\n -> {output_dir}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()