export type ExerciseMode = 'PUSH-UP' | 'SQUAT' | 'SIT-UP' | 'AUTO';

/** [xNorm (0..1), yNorm (0..1), confidence (0..1)] */
export type NormalizedKeypoint = [number, number, number];

export interface PalmPoint {
  label: 'Left' | 'Right' | string;
  wrist: [number, number];
  palm: [number, number];
}

export interface PersonTelemetry {
  track_id: number;
  rank: number;
  rep_count: number;
  clean_reps: number;
  bad_reps: number;
  depth_pct: number;
  stage: string;
  status: string;
  primary_angle: number;
  posture_angle: number;
  exercise: string;
  edges: [number, number][];
  keypoints: NormalizedKeypoint[];
  palms: PalmPoint[];
}

export interface TelemetryPacket {
  type: 'telemetry';
  ts?: number;
  infer_ms?: number;
  fps: number;
  active_mode: ExerciseMode;
  frame_w: number;
  frame_h: number;
  persons: PersonTelemetry[];
}

export type WebSocketServerMessage =
  | TelemetryPacket
  | { type: 'connected'; active_mode: ExerciseMode; imgsz: number }
  | { type: 'mode_updated'; active_mode: ExerciseMode }
  | { type: 'reset_done' }
  | { type: 'pong'; ts?: number }
  | { type: 'error'; message: string };
