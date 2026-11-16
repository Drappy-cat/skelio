import React from 'react';
import { StyleSheet } from 'react-native';
import Svg, { Circle, Line, Rect, Text as SvgText } from 'react-native-svg';
import type { PersonTelemetry } from '../engine/types';

interface SkeletonOverlayProps {
  width: number;
  height: number;
  persons: PersonTelemetry[];
}

const PERSON_COLORS = ['#00e6ff', '#50ff50', '#ff8c00'];
const CONF_THRESHOLD = 0.35;

export const SkeletonOverlay: React.FC<SkeletonOverlayProps> = ({ width, height, persons }) => {
  if (width <= 0 || height <= 0 || persons.length === 0) {
    return null;
  }

  return (
    <Svg width={width} height={height} style={StyleSheet.absoluteFill} pointerEvents="none">
      {persons.map((person, pIdx) => {
        const color = PERSON_COLORS[Math.min(pIdx, PERSON_COLORS.length - 1)];
        const kpts = person.keypoints;
        const validIndices: number[] = [];

        for (let i = 0; i < kpts.length; i++) {
          const [nx, ny, conf] = kpts[i];
          if (conf >= CONF_THRESHOLD && nx > 0.005 && nx < 0.995 && ny > 0.005 && ny < 0.995) {
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
            if (px < minX) minX = px;
            if (py < minY) minY = py;
            if (px > maxX) maxX = px;
            if (py > maxY) maxY = py;
          }
          const x0 = Math.max(2, minX - 14);
          const y0 = Math.max(2, minY - 18);
          const x1 = Math.min(width - 2, maxX + 14);
          const y1 = Math.min(height - 2, maxY + 14);
          bbox = { x: x0, y: y0, w: Math.max(10, x1 - x0), h: Math.max(10, y1 - y0) };
        }

        const validSet = new Set(validIndices);

        return (
          <React.Fragment key={`person-${person.track_id}`}>
            {bbox && (
              <>
                <Rect
                  x={bbox.x}
                  y={bbox.y}
                  width={bbox.w}
                  height={bbox.h}
                  stroke={color}
                  strokeWidth={1.5}
                  strokeDasharray="6 4"
                  fill="none"
                />
                <SvgText
                  x={bbox.x + 6}
                  y={Math.max(14, bbox.y - 6)}
                  fill={color}
                  fontSize="11"
                  fontWeight="bold">
                  {`P${person.rank} • ${person.exercise}`}
                </SvgText>
              </>
            )}

            {person.edges.map(([i1, i2], eIdx) => {
              if (!validSet.has(i1) || !validSet.has(i2)) {
                return null;
              }
              return (
                <Line
                  key={`edge-${person.track_id}-${eIdx}`}
                  x1={kpts[i1][0] * width}
                  y1={kpts[i1][1] * height}
                  x2={kpts[i2][0] * width}
                  y2={kpts[i2][1] * height}
                  stroke={color}
                  strokeWidth={3}
                  strokeLinecap="round"
                />
              );
            })}

            {validIndices.map(idx => (
              <Circle
                key={`kpt-${person.track_id}-${idx}`}
                cx={kpts[idx][0] * width}
                cy={kpts[idx][1] * height}
                r={5}
                fill={color}
                stroke="#0b0f19"
                strokeWidth={1.5}
              />
            ))}

            {person.palms.map((palm, idx) => (
              <React.Fragment key={`palm-${person.track_id}-${idx}`}>
                <Line
                  x1={palm.wrist[0] * width}
                  y1={palm.wrist[1] * height}
                  x2={palm.palm[0] * width}
                  y2={palm.palm[1] * height}
                  stroke="#38bdf8"
                  strokeWidth={2.5}
                />
                <Circle
                  cx={palm.palm[0] * width}
                  cy={palm.palm[1] * height}
                  r={6}
                  fill="#22c55e"
                  stroke="#052e16"
                  strokeWidth={1.5}
                />
              </React.Fragment>
            ))}
          </React.Fragment>
        );
      })}
    </Svg>
  );
};
