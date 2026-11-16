import React, { useEffect, useRef, useState } from 'react';
import {
  Modal,
  Pressable,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import {
  Camera,
  type CameraRef,
  useCameraDevice,
  useCameraPermission,
} from 'react-native-vision-camera';
import type { Image as NitroImage } from 'react-native-nitro-image';
import { SkeletonOverlay } from './components/SkeletonOverlay';
import type { ExerciseMode } from './engine/types';
import { usePoseWebSocket } from './hooks/usePoseWebSocket';

const MODES: ExerciseMode[] = ['PUSH-UP', 'SQUAT', 'SIT-UP', 'AUTO'];
const DEFAULT_WS_URL = 'ws://192.168.1.31:8000/ws/pose';
const TARGET_STREAM_WIDTH = 320;
const JPEG_QUALITY = 60;

export function App() {
  return (
    <SafeAreaProvider>
      <StatusBar barStyle="light-content" />
      <SkelioNativeScreen />
    </SafeAreaProvider>
  );
}

function SkelioNativeScreen() {
  const { hasPermission, requestPermission } = useCameraPermission();
  const [cameraPosition, setCameraPosition] = useState<'front' | 'back'>('front');
  const device = useCameraDevice(cameraPosition);

  const [wsUrl, setWsUrl] = useState<string>(DEFAULT_WS_URL);
  const [draftUrl, setDraftUrl] = useState<string>(DEFAULT_WS_URL);
  const [serverModalVisible, setServerModalVisible] = useState<boolean>(false);
  const [previewReady, setPreviewReady] = useState<boolean>(false);
  const [viewport, setViewport] = useState<{ width: number; height: number }>({
    width: 0,
    height: 0,
  });

  const cameraRef = useRef<CameraRef>(null);
  const {
    status,
    activeMode,
    persons,
    fps,
    rttMs,
    inferMs,
    canSendFrame,
    sendFrame,
    setMode,
    resetReps,
  } = usePoseWebSocket(wsUrl);

  useEffect(() => {
    if (!hasPermission) {
      requestPermission();
    }
  }, [hasPermission, requestPermission]);

  // Split-Pipeline Capture Loop:
  // Hanya mengambil snapshot saat WebSocket terhubung dan slot inferensi (Queue=1) kosong.
  useEffect(() => {
    if (!hasPermission || !device || !previewReady || status !== 'connected') {
      return;
    }

    let cancelled = false;
    let capturing = false;

    const tick = async () => {
      if (cancelled || capturing || !cameraRef.current || !canSendFrame()) {
        return;
      }

      capturing = true;
      let rawImage: NitroImage | null = null;
      let resizedImage: NitroImage | null = null;

      try {
        rawImage = await cameraRef.current.takeSnapshot();
        if (cancelled) {
          return;
        }

        const scale = TARGET_STREAM_WIDTH / Math.max(1, rawImage.width);
        const targetH = Math.max(180, Math.round(rawImage.height * scale));
        resizedImage = await rawImage.resizeAsync(TARGET_STREAM_WIDTH, targetH);
        const encoded = await resizedImage.toEncodedImageDataAsync('jpg', JPEG_QUALITY);

        if (!cancelled) {
          sendFrame(encoded.buffer);
        }
      } catch {
        // Preview sementara belum siap atau camera sedang beralih posisi
      } finally {
        try {
          resizedImage?.dispose();
        } catch {}
        try {
          rawImage?.dispose();
        } catch {}
        capturing = false;
      }
    };

    const timer = setInterval(tick, 33);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [hasPermission, device, previewReady, status, canSendFrame, sendFrame]);

  const primary = persons[0];
  const depthPct = primary ? Math.min(100, Math.max(0, primary.depth_pct)) : 0;
  const statusColor =
    status === 'connected' ? '#22c55e' : status === 'connecting' ? '#f59e0b' : '#ef4444';
  const postureText = primary?.status ?? 'POSISIKAN TUBUH TERLIHAT';
  const postureFault =
    postureText.includes('TURUN') || postureText.includes('BUNGKUK');

  return (
    <SafeAreaView style={styles.root}>
      {/* Top Bar */}
      <View style={styles.topBar}>
        <View>
          <Text style={styles.brandTitle}>SKELIO NATIVE v3.0</Text>
          <View style={styles.connRow}>
            <View style={[styles.dot, { backgroundColor: statusColor }]} />
            <Text style={styles.connLabel}>
              {status === 'connected'
                ? `LIVE • RTT ${rttMs}ms (AI ${inferMs}ms) • ${fps.toFixed(1)} FPS`
                : status === 'connecting'
                ? 'Menghubungkan ke FastAPI...'
                : 'Terputus (Cek IP Server)'}
            </Text>
          </View>
        </View>

        <View style={styles.topActions}>
          <Pressable
            onPress={() => setCameraPosition(prev => (prev === 'front' ? 'back' : 'front'))}
            style={styles.iconBtn}>
            <Text style={styles.iconBtnText}>
              {cameraPosition === 'front' ? 'Kamera Depan' : 'Kamera Blkg'}
            </Text>
          </Pressable>
          <Pressable
            onPress={() => {
              setDraftUrl(wsUrl);
              setServerModalVisible(true);
            }}
            style={styles.iconBtn}>
            <Text style={styles.iconBtnText}>Server IP</Text>
          </Pressable>
        </View>
      </View>

      {/* Camera Viewport + SVG Skeleton Overlay */}
      <View
        style={styles.cameraStage}
        onLayout={e => {
          const { width, height } = e.nativeEvent.layout;
          setViewport({ width, height });
        }}>
        {!hasPermission ? (
          <View style={styles.permissionCard}>
            <Text style={styles.permissionTitle}>Izin Kamera Diperlukan</Text>
            <Text style={styles.permissionSub}>
              SKELIO membutuhkan akses kamera untuk evaluasi postur biomekanika real-time.
            </Text>
            <Pressable onPress={requestPermission} style={styles.primaryBtn}>
              <Text style={styles.primaryBtnText}>Izinkan Kamera</Text>
            </Pressable>
          </View>
        ) : !device ? (
          <View style={styles.permissionCard}>
            <Text style={styles.permissionTitle}>Kamera Tidak Ditemukan</Text>
          </View>
        ) : (
          <>
            <Camera
              ref={cameraRef}
              style={StyleSheet.absoluteFill}
              device={device}
              isActive={true}
              implementationMode="compatible"
              resizeMode="cover"
              onPreviewStarted={() => setPreviewReady(true)}
              onPreviewStopped={() => setPreviewReady(false)}
            />
            <SkeletonOverlay
              width={viewport.width}
              height={viewport.height}
              persons={persons}
            />
          </>
        )}

        {/* Right-edge Vertical Depth Gauge */}
        <View style={styles.depthTrack}>
          <View
            style={[
              styles.depthFill,
              {
                height: `${depthPct}%`,
                backgroundColor:
                  depthPct >= 70 ? '#22c55e' : depthPct >= 35 ? '#f59e0b' : '#ef4444',
              },
            ]}
          />
        </View>

        {/* Top-left Mode Badge */}
        <View style={styles.modeBadge}>
          <Text style={styles.modeBadgeText}>{activeMode}</Text>
          <Text style={styles.stageBadgeText}>{primary?.stage ?? 'IDLE'}</Text>
        </View>
      </View>

      {/* Telemetry & Controls */}
      <View style={styles.bottomPanel}>
        <View style={styles.metricsRow}>
          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>REPETISI</Text>
            <Text style={styles.metricValue}>{primary?.rep_count ?? 0}</Text>
            <Text style={styles.metricSub}>Clean: {primary?.clean_reps ?? 0}</Text>
          </View>
          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>SUDUT</Text>
            <Text style={[styles.metricValue, { color: '#22d3ee' }]}>
              {Math.round(primary?.primary_angle ?? 0)}°
            </Text>
            <Text style={styles.metricSub}>
              Postur: {Math.round(primary?.posture_angle ?? 0)}°
            </Text>
          </View>
          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>KEDALAMAN</Text>
            <Text style={[styles.metricValue, { color: '#fbbf24' }]}>
              {Math.round(depthPct)}%
            </Text>
            <Text style={styles.metricSub}>Target 70%+</Text>
          </View>
        </View>

        <View
          style={[
            styles.postureBanner,
            { borderColor: postureFault ? '#ef4444' : '#1e293b' },
          ]}>
          <Text
            numberOfLines={1}
            style={[
              styles.postureText,
              { color: postureFault ? '#f87171' : '#34d399' },
            ]}>
            {postureText}
          </Text>
        </View>

        <View style={styles.modeRow}>
          {MODES.map(mode => {
            const active = activeMode === mode;
            return (
              <Pressable
                key={mode}
                onPress={() => setMode(mode)}
                style={[styles.modePill, active && styles.modePillActive]}>
                <Text style={[styles.modePillText, active && styles.modePillTextActive]}>
                  {mode}
                </Text>
              </Pressable>
            );
          })}
          <Pressable onPress={resetReps} style={styles.resetBtn}>
            <Text style={styles.resetBtnText}>Reset</Text>
          </Pressable>
        </View>
      </View>

      {/* Server WebSocket Config Modal */}
      <Modal
        visible={serverModalVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setServerModalVisible(false)}>
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Alamat Server FastAPI WebSocket</Text>
            <Text style={styles.modalDesc}>
              Pastikan HP & Laptop terhubung di Wi-Fi yang sama, lalu jalankan{' '}
              run_skelio_api.bat.
            </Text>
            <TextInput
              value={draftUrl}
              onChangeText={setDraftUrl}
              placeholder="ws://192.168.1.31:8000/ws/pose"
              placeholderTextColor="#64748b"
              autoCapitalize="none"
              autoCorrect={false}
              style={styles.input}
            />
            <View style={styles.modalActions}>
              <Pressable
                onPress={() => setServerModalVisible(false)}
                style={styles.cancelBtn}>
                <Text style={styles.cancelBtnText}>Batal</Text>
              </Pressable>
              <Pressable
                onPress={() => {
                  const trimmed = draftUrl.trim();
                  if (trimmed) {
                    setWsUrl(trimmed);
                  }
                  setServerModalVisible(false);
                }}
                style={styles.primaryBtn}>
                <Text style={styles.primaryBtnText}>Hubungkan</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#0b0f19' },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 10,
    backgroundColor: '#0f172a',
    borderBottomWidth: 1,
    borderBottomColor: '#1e293b',
  },
  brandTitle: { color: '#22d3ee', fontSize: 15, fontWeight: '800', letterSpacing: 0.4 },
  connRow: { flexDirection: 'row', alignItems: 'center', marginTop: 2, gap: 6 },
  dot: { width: 8, height: 8, borderRadius: 4 },
  connLabel: { color: '#94a3b8', fontSize: 11, fontFamily: 'monospace' },
  topActions: { flexDirection: 'row', gap: 6 },
  iconBtn: {
    backgroundColor: '#1e293b',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#334155',
  },
  iconBtnText: { color: '#e2e8f0', fontSize: 11, fontWeight: '600' },

  cameraStage: {
    flex: 1,
    margin: 10,
    borderRadius: 18,
    overflow: 'hidden',
    backgroundColor: '#020617',
    borderWidth: 1,
    borderColor: '#1e293b',
    justifyContent: 'center',
    alignItems: 'center',
  },
  permissionCard: { padding: 24, alignItems: 'center', gap: 10 },
  permissionTitle: { color: '#f8fafc', fontSize: 16, fontWeight: '700' },
  permissionSub: { color: '#94a3b8', fontSize: 13, textAlign: 'center' },
  primaryBtn: {
    backgroundColor: '#06b6d4',
    paddingHorizontal: 16,
    paddingVertical: 9,
    borderRadius: 10,
  },
  primaryBtnText: { color: '#082f49', fontWeight: '800', fontSize: 13 },

  depthTrack: {
    position: 'absolute',
    right: 10,
    top: 16,
    bottom: 16,
    width: 12,
    borderRadius: 6,
    backgroundColor: 'rgba(15, 23, 42, 0.75)',
    borderWidth: 1,
    borderColor: '#334155',
    justifyContent: 'flex-end',
    padding: 2,
  },
  depthFill: { width: '100%', borderRadius: 4 },

  modeBadge: {
    position: 'absolute',
    top: 12,
    left: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: 'rgba(15, 23, 42, 0.85)',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#334155',
  },
  modeBadgeText: { color: '#22d3ee', fontSize: 12, fontWeight: '800' },
  stageBadgeText: { color: '#f8fafc', fontSize: 11, fontWeight: '700' },

  bottomPanel: {
    paddingHorizontal: 12,
    paddingBottom: 12,
    gap: 8,
  },
  metricsRow: { flexDirection: 'row', gap: 8 },
  metricCard: {
    flex: 1,
    backgroundColor: '#111827',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#1e293b',
    paddingVertical: 8,
    paddingHorizontal: 6,
    alignItems: 'center',
  },
  metricLabel: { color: '#94a3b8', fontSize: 10, fontWeight: '700' },
  metricValue: { color: '#ffffff', fontSize: 26, fontWeight: '800', marginVertical: 2 },
  metricSub: { color: '#64748b', fontSize: 10 },

  postureBanner: {
    backgroundColor: '#111827',
    borderWidth: 1,
    borderRadius: 10,
    paddingVertical: 8,
    paddingHorizontal: 12,
    alignItems: 'center',
  },
  postureText: { fontSize: 12, fontWeight: '800', letterSpacing: 0.3 },

  modeRow: { flexDirection: 'row', gap: 6, alignItems: 'center' },
  modePill: {
    flex: 1,
    paddingVertical: 9,
    borderRadius: 10,
    backgroundColor: '#1e293b',
    alignItems: 'center',
  },
  modePillActive: { backgroundColor: '#06b6d4' },
  modePillText: { color: '#cbd5e1', fontSize: 11, fontWeight: '700' },
  modePillTextActive: { color: '#082f49', fontWeight: '800' },
  resetBtn: {
    paddingHorizontal: 12,
    paddingVertical: 9,
    borderRadius: 10,
    backgroundColor: '#334155',
    alignItems: 'center',
  },
  resetBtnText: { color: '#f8fafc', fontSize: 11, fontWeight: '700' },

  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(2, 6, 23, 0.8)',
    justifyContent: 'center',
    padding: 20,
  },
  modalCard: {
    backgroundColor: '#0f172a',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#334155',
    padding: 18,
    gap: 10,
  },
  modalTitle: { color: '#f8fafc', fontSize: 15, fontWeight: '800' },
  modalDesc: { color: '#94a3b8', fontSize: 12 },
  input: {
    backgroundColor: '#020617',
    borderWidth: 1,
    borderColor: '#334155',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: '#f8fafc',
    fontSize: 13,
  },
  modalActions: { flexDirection: 'row', justifyContent: 'flex-end', gap: 10, marginTop: 4 },
  cancelBtn: { paddingHorizontal: 14, paddingVertical: 9, borderRadius: 10, backgroundColor: '#1e293b' },
  cancelBtnText: { color: '#cbd5e1', fontSize: 13, fontWeight: '600' },
});

export default App;
