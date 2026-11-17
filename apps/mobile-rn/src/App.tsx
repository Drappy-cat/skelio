import React, { useEffect, useRef, useState } from 'react';
import {
  Modal,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  useWindowDimensions,
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
const TARGET_STREAM_WIDTH = 256;
const JPEG_QUALITY = 50;
const sleep = (ms: number): Promise<void> =>
  new Promise(resolve => setTimeout(() => resolve(), ms));

export function App() {
  return (
    <SafeAreaProvider>
      <StatusBar barStyle="light-content" />
      <SkelioNativeScreen />
    </SafeAreaProvider>
  );
}

function SkelioNativeScreen() {
  const { width, height } = useWindowDimensions();
  const isLandscape = width > height;

  const { hasPermission, requestPermission } = useCameraPermission();
  const [cameraPosition, setCameraPosition] = useState<'front' | 'back'>('front');
  const device = useCameraDevice(cameraPosition);

  const [wsUrl, setWsUrl] = useState<string>(DEFAULT_WS_URL);
  const [draftUrl, setDraftUrl] = useState<string>(DEFAULT_WS_URL);
  const [serverModalVisible, setServerModalVisible] = useState<boolean>(false);
  const [panelVisible, setPanelVisible] = useState<boolean>(true);
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
    queueOrSendFrame,
    setMode,
    resetReps,
  } = usePoseWebSocket(wsUrl);

  useEffect(() => {
    if (!hasPermission) {
      requestPermission();
    }
  }, [hasPermission, requestPermission]);

  // Pipelined Capture Loop:
  // Capture + resize + encode JPEG frame berikutnya di HP berjalan paralel dengan inferensi server.
  useEffect(() => {
    if (!hasPermission || !device || !previewReady || status !== 'connected') {
      return;
    }

    let cancelled = false;

    const runPipeline = async () => {
      while (!cancelled) {
        if (!cameraRef.current) {
          await sleep(16);
          continue;
        }

        let rawImage: NitroImage | null = null;
        let resizedImage: NitroImage | null = null;

        try {
          rawImage = await cameraRef.current.takeSnapshot();
          if (cancelled) {
            break;
          }

          const scale = TARGET_STREAM_WIDTH / Math.max(1, rawImage.width);
          const targetH = Math.max(144, Math.round(rawImage.height * scale));
          resizedImage = await rawImage.resizeAsync(TARGET_STREAM_WIDTH, targetH);
          const encoded = await resizedImage.toEncodedImageDataAsync('jpg', JPEG_QUALITY);

          if (!cancelled) {
            queueOrSendFrame(encoded.buffer);
          }
        } catch {
          // Preview sementara belum siap atau camera sedang beralih posisi
          await sleep(16);
        } finally {
          try {
            resizedImage?.dispose();
          } catch {}
          try {
            rawImage?.dispose();
          } catch {}
        }

        // Beri jeda singkat agar UI/gesture thread tetap responsif
        await sleep(4);
      }
    };

    runPipeline();
    return () => {
      cancelled = true;
    };
  }, [hasPermission, device, previewReady, status, queueOrSendFrame]);

  const primary = persons[0];
  const depthPct = primary ? Math.min(100, Math.max(0, primary.depth_pct)) : 0;
  const statusColor =
    status === 'connected' ? '#22c55e' : status === 'connecting' ? '#f59e0b' : '#ef4444';
  const postureText = primary?.status ?? 'POSISIKAN TUBUH TERLIHAT';
  const postureFault =
    postureText.includes('TURUN') || postureText.includes('BUNGKUK');

  const sidePanelWidth = Math.min(245, Math.max(198, Math.round(width * 0.27)));

  const renderControlPanel = () => (
    <View
      style={[
        styles.controlPanel,
        isLandscape
          ? [styles.controlPanelLandscape, { width: sidePanelWidth }]
          : styles.controlPanelPortrait,
      ]}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.panelScrollContent}>
        {/* Quick Actions: Camera & Server IP */}
        <View style={styles.utilityRow}>
          <Pressable
            onPress={() => setCameraPosition(prev => (prev === 'front' ? 'back' : 'front'))}
            style={styles.utilityBtn}>
            <Text style={styles.utilityBtnText}>
              {cameraPosition === 'front' ? 'Kamera: Depan' : 'Kamera: Blkg'}
            </Text>
          </Pressable>
          <Pressable
            onPress={() => {
              setDraftUrl(wsUrl);
              setServerModalVisible(true);
            }}
            style={styles.utilityBtn}>
            <Text style={styles.utilityBtnText}>Server IP</Text>
          </Pressable>
        </View>

        {/* Live Telemetry Cards */}
        <View style={styles.metricsRow}>
          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>REPS</Text>
            <Text style={[styles.metricValue, isLandscape && styles.metricValueCompact]}>
              {primary?.rep_count ?? 0}
            </Text>
            <Text style={styles.metricSub}>Clean {primary?.clean_reps ?? 0}</Text>
          </View>
          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>SUDUT</Text>
            <Text
              style={[
                styles.metricValue,
                isLandscape && styles.metricValueCompact,
                { color: '#22d3ee' },
              ]}>
              {Math.round(primary?.primary_angle ?? 0)}°
            </Text>
            <Text style={styles.metricSub}>Post {Math.round(primary?.posture_angle ?? 0)}°</Text>
          </View>
          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>DEPTH</Text>
            <Text
              style={[
                styles.metricValue,
                isLandscape && styles.metricValueCompact,
                { color: '#fbbf24' },
              ]}>
              {Math.round(depthPct)}%
            </Text>
            <Text style={styles.metricSub}>Target 70%</Text>
          </View>
        </View>

        {/* Posture Callout */}
        <View
          style={[
            styles.postureBanner,
            { borderColor: postureFault ? '#ef4444' : '#1e293b' },
          ]}>
          <Text
            numberOfLines={2}
            style={[
              styles.postureText,
              { color: postureFault ? '#f87171' : '#34d399' },
            ]}>
            {postureText}
          </Text>
        </View>

        {/* Adaptive Mode Buttons (2x2 Grid in Landscape, Single Row in Portrait) */}
        <View style={isLandscape ? styles.modeGridLandscape : styles.modeRowPortrait}>
          {MODES.map(mode => {
            const active = activeMode === mode;
            return (
              <Pressable
                key={mode}
                onPress={() => setMode(mode)}
                style={[
                  styles.modePill,
                  isLandscape ? styles.modePillGrid : styles.modePillRow,
                  active && styles.modePillActive,
                ]}>
                <Text style={[styles.modePillText, active && styles.modePillTextActive]}>
                  {mode}
                </Text>
              </Pressable>
            );
          })}
          <Pressable
            onPress={resetReps}
            style={[styles.resetBtn, isLandscape && styles.resetBtnFull]}>
            <Text style={styles.resetBtnText}>Reset Repetisi</Text>
          </Pressable>
        </View>
      </ScrollView>
    </View>
  );

  return (
    <SafeAreaView style={styles.root}>
      <View
        style={[
          styles.mainContainer,
          { flexDirection: isLandscape ? 'row' : 'column' },
        ]}>
        {/* Camera Viewport (Mengambil area utama seluas mungkin) */}
        <View
          style={styles.cameraStage}
          onLayout={e => {
            const { width: vw, height: vh } = e.nativeEvent.layout;
            setViewport({ width: vw, height: vh });
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

          {/* Floating Top-Left HUD: Connection + Active Mode */}
          <View style={styles.floatingTopLeft}>
            <View style={styles.connPill}>
              <View style={[styles.dot, { backgroundColor: statusColor }]} />
              <Text style={styles.connPillText}>
                {status === 'connected'
                  ? `LIVE • ${rttMs}ms (AI ${inferMs}ms) • ${fps.toFixed(1)} FPS`
                  : status === 'connecting'
                  ? 'Menghubungkan...'
                  : 'Terputus'}
              </Text>
            </View>
            <View style={styles.modeBadge}>
              <Text style={styles.modeBadgeText}>{activeMode}</Text>
              <Text style={styles.stageBadgeText}>{primary?.stage ?? 'IDLE'}</Text>
            </View>
          </View>

          {/* Floating Top-Right Toggle: Hide / Show Control Panel */}
          <Pressable
            onPress={() => setPanelVisible(prev => !prev)}
            style={styles.togglePanelBtn}>
            <Text style={styles.togglePanelBtnText}>
              {panelVisible ? 'Sembunyikan' : 'Menu Kontrol'}
            </Text>
          </Pressable>

          {/* Mini Floating Metrics when Panel is Hidden (Fullscreen Mode) */}
          {!panelVisible && (
            <View style={styles.miniHudBottomLeft}>
              <Text style={styles.miniHudText}>
                {`REPS: ${primary?.rep_count ?? 0}  •  SUDUT: ${Math.round(
                  primary?.primary_angle ?? 0,
                )}°  •  ${postureText}`}
              </Text>
            </View>
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
        </View>

        {/* Adaptive Side / Bottom Control Panel */}
        {panelVisible && renderControlPanel()}
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
  mainContainer: { flex: 1 },

  cameraStage: {
    flex: 1,
    margin: 6,
    borderRadius: 16,
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

  floatingTopLeft: {
    position: 'absolute',
    top: 10,
    left: 10,
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    gap: 6,
    maxWidth: '72%',
  },
  connPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(15, 23, 42, 0.78)',
    paddingHorizontal: 9,
    paddingVertical: 5,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(51, 65, 85, 0.8)',
  },
  dot: { width: 7, height: 7, borderRadius: 4 },
  connPillText: { color: '#e2e8f0', fontSize: 10, fontFamily: 'monospace', fontWeight: '600' },
  modeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(15, 23, 42, 0.78)',
    paddingHorizontal: 9,
    paddingVertical: 5,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(51, 65, 85, 0.8)',
  },
  modeBadgeText: { color: '#22d3ee', fontSize: 11, fontWeight: '800' },
  stageBadgeText: { color: '#f8fafc', fontSize: 10, fontWeight: '700' },

  togglePanelBtn: {
    position: 'absolute',
    top: 10,
    right: 10,
    backgroundColor: 'rgba(15, 23, 42, 0.82)',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#334155',
  },
  togglePanelBtnText: { color: '#38bdf8', fontSize: 11, fontWeight: '700' },

  miniHudBottomLeft: {
    position: 'absolute',
    bottom: 12,
    left: 12,
    right: 34,
    backgroundColor: 'rgba(15, 23, 42, 0.82)',
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#334155',
  },
  miniHudText: { color: '#f8fafc', fontSize: 12, fontWeight: '700' },

  depthTrack: {
    position: 'absolute',
    right: 10,
    top: 48,
    bottom: 14,
    width: 10,
    borderRadius: 5,
    backgroundColor: 'rgba(15, 23, 42, 0.72)',
    borderWidth: 1,
    borderColor: '#334155',
    justifyContent: 'flex-end',
    padding: 2,
  },
  depthFill: { width: '100%', borderRadius: 4 },

  controlPanel: {
    backgroundColor: '#0f172a',
    borderColor: '#1e293b',
  },
  controlPanelLandscape: {
    height: '100%',
    borderLeftWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
  controlPanelPortrait: {
    width: '100%',
    borderTopWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
  panelScrollContent: {
    gap: 8,
  },

  utilityRow: { flexDirection: 'row', gap: 6 },
  utilityBtn: {
    flex: 1,
    backgroundColor: '#1e293b',
    paddingVertical: 7,
    paddingHorizontal: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#334155',
    alignItems: 'center',
  },
  utilityBtnText: { color: '#e2e8f0', fontSize: 11, fontWeight: '700' },

  metricsRow: { flexDirection: 'row', gap: 6 },
  metricCard: {
    flex: 1,
    backgroundColor: '#111827',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#1e293b',
    paddingVertical: 6,
    paddingHorizontal: 4,
    alignItems: 'center',
  },
  metricLabel: { color: '#94a3b8', fontSize: 9, fontWeight: '700' },
  metricValue: { color: '#ffffff', fontSize: 22, fontWeight: '800', marginVertical: 1 },
  metricValueCompact: { fontSize: 18 },
  metricSub: { color: '#64748b', fontSize: 9 },

  postureBanner: {
    backgroundColor: '#111827',
    borderWidth: 1,
    borderRadius: 8,
    paddingVertical: 6,
    paddingHorizontal: 8,
    alignItems: 'center',
  },
  postureText: { fontSize: 11, fontWeight: '800', textAlign: 'center' },

  modeGridLandscape: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  modeRowPortrait: {
    flexDirection: 'row',
    gap: 6,
    alignItems: 'center',
  },
  modePill: {
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: '#1e293b',
    alignItems: 'center',
  },
  modePillGrid: {
    width: '48%',
  },
  modePillRow: {
    flex: 1,
  },
  modePillActive: { backgroundColor: '#06b6d4' },
  modePillText: { color: '#cbd5e1', fontSize: 11, fontWeight: '700' },
  modePillTextActive: { color: '#082f49', fontWeight: '800' },

  resetBtn: {
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: '#334155',
    alignItems: 'center',
  },
  resetBtnFull: {
    width: '100%',
    marginTop: 2,
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
