import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import type { PersonTelemetry } from '../engine/types';

interface SkeletonOverlayProps {
  width: number;
  height: number;
  persons: PersonTelemetry[];
}

const PERSON_COLORS = ['#00e6ff', '#50ff50', '#ff8c00'];
const CONF_THRESHOLD = 0.35;

interface SegmentLineProps {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  color: string;
  thickness?: number;
}

const SegmentLine: React.FC<SegmentLineProps> = ({
  x1,
  y1,
  x2,
  y2,
  color,
  thickness = 3,
}) => {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const length = Math.hypot(dx, dy);
  if (length < 1) {
    return null;
  }
  const angleRad = Math.atan2(dy, dx);
  const cx = (x1 + x2) / 2;
  const cy = (y1 + y2) / 2;

  return (
    <View
      style={{
        position: 'absolute',
        left: cx - length / 2,
        top: cy - thickness / 2,
        width: length,
        height: thickness,
        borderRadius: thickness / 2,
        backgroundColor: color,
        transform: [{ rotate: `${angleRad}rad` }],
      }}
    />
  );
};

export const SkeletonOverlay: React.FC<SkeletonOverlayProps> = ({
  width,
  height,
  persons,
}) => {
  if (width <= 0 || height <= 0 || persons.length === 0) {
    return null;
  }

  return (
    <View style={StyleSheet.absoluteFill} pointerEvents="none">
      {persons.map((person, pIdx) => {
        const color = PERSON_COLORS[Math.min(pIdx, PERSON_COLORS.length - 1)];
        const kpts = person.keypoints;
        const validIndices: number[] = [];

        for (let i = 0; i < kpts.length; i++) {
          const [nx, ny, conf] = kpts[i];
          if (
            conf >= CONF_THRESHOLD &&
            nx > 0.005 &&
            nx < 0.995 &&
            ny > 0.005 &&
            ny < 0.995
          ) {
            validIndices.push(i);
          }
        }

        let bbox: { x: number; y: number; w: number; h: number } | null = null;
        if (validIndices.length >= 4) {
          let minX = width;
          let minY = height;
          let maxX = 0;
          let maxY = 0;
          for (const idx of validIndices) {
            const px = kpts[idx][0] * width;
            const py = kpts[idx][1] * height;
            if (px < minX) {
              minX = px;
            }
            if (py < minY) {
              minY = py;
            }
            if (px > maxX) {
              maxX = px;
            }
            if (py > maxY) {
              maxY = py;
            }
          }
          const x0 = Math.max(2, minX - 14);
          const y0 = Math.max(2, minY - 18);
          const x1 = Math.min(width - 2, maxX + 14);
          const y1 = Math.min(height - 2, maxY + 14);
          bbox = {
            x: x0,
            y: y0,
            w: Math.max(10, x1 - x0),
            h: Math.max(10, y1 - y0),
          };
        }

        const validSet = new Set(validIndices);

        return (
          <React.Fragment key={`person-${person.track_id}`}>
            {bbox && (
              <>
                <View
                  style={[
                    styles.bbox,
                    {
                      left: bbox.x,
                      top: bbox.y,
                      width: bbox.w,
                      height: bbox.h,
                      borderColor: color,
                    },
                  ]}
                />
                <Text
                  style={[
                    styles.bboxLabel,
                    {
                      left: bbox.x + 4,
                      top: Math.max(4, bbox.y - 16),
                      color,
                    },
                  ]}>
                  {`P${person.rank} • ${person.exercise}`}
                </Text>
              </>
            )}

            {person.edges.map(([i1, i2], eIdx) => {
              if (!validSet.has(i1) || !validSet.has(i2)) {
                return null;
              }
              return (
                <SegmentLine
                  key={`edge-${person.track_id}-${eIdx}`}
                  x1={kpts[i1][0] * width}
                  y1={kpts[i1][1] * height}
                  x2={kpts[i2][0] * width}
                  y2={kpts[i2][1] * height}
                  color={color}
                  thickness={3}
                />
              );
            })}

            {validIndices.map(idx => {
              const cx = kpts[idx][0] * width;
              const cy = kpts[idx][1] * height;
              return (
                <View
                  key={`kpt-${person.track_id}-${idx}`}
                  style={[
                    styles.keypointDot,
                    {
                      left: cx - 5,
                      top: cy - 5,
                      backgroundColor: color,
                    },
                  ]}
                />
              );
            })}

            {person.palms.map((palm, idx) => {
              const px = palm.palm[0] * width;
              const py = palm.palm[1] * height;
              return (
                <React.Fragment key={`palm-${person.track_id}-${idx}`}>
                  <SegmentLine
                    x1={palm.wrist[0] * width}
                    y1={palm.wrist[1] * height}
                    x2={px}
                    y2={py}
                    color="#38bdf8"
                    thickness={2.5}
                  />
                  <View
                    style={[
                      styles.palmDot,
                      {
                        left: px - 6,
                        top: py - 6,
                      },
                    ]}
                  />
                </React.Fragment>
              );
            })}
          </React.Fragment>
        );
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  bbox: {
    position: 'absolute',
    borderWidth: 1.5,
    borderStyle: 'dashed',
    borderRadius: 6,
  },
  bboxLabel: {
    position: 'absolute',
    fontSize: 11,
    fontWeight: '800',
    backgroundColor: 'rgba(11, 15, 25, 0.72)',
    paddingHorizontal: 5,
    paddingVertical: 1,
    borderRadius: 4,
  },
  keypointDot: {
    position: 'absolute',
    width: 10,
    height: 10,
    borderRadius: 5,
    borderWidth: 1.5,
    borderColor: '#0b0f19',
  },
  palmDot: {
    position: 'absolute',
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#22c55e',
    borderWidth: 1.5,
    borderColor: '#052e16',
  },
});
