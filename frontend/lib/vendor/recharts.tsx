"use client";

import React from "react";

type ChartPoint = Record<string, number | string>;

type ResponsiveContainerProps = {
  width?: string | number;
  height?: string | number;
  children: React.ReactNode;
};

type RadarChartProps = {
  data: ChartPoint[];
  children: React.ReactNode;
};

type PolarAngleAxisProps = {
  dataKey: string;
};

type PolarRadiusAxisProps = {
  domain?: [number, number];
  tick?: boolean;
};

type RadarProps = {
  dataKey: string;
  stroke?: string;
  fill?: string;
  fillOpacity?: number;
};

const CX = 200;
const CY = 160;
const MAX_R = 115;

function vertex(index: number, total: number, radius: number) {
  const angle = -Math.PI / 2 + (index * (Math.PI * 2)) / total;
  return {
    x: CX + Math.cos(angle) * radius,
    y: CY + Math.sin(angle) * radius,
  };
}

export function ResponsiveContainer({ width = "100%", height = 350, children }: ResponsiveContainerProps) {
  return (
    <div style={{ width, height }}>
      {children}
    </div>
  );
}

export function PolarGrid() {
  return null;
}

PolarGrid.displayName = "PolarGrid";

export function PolarAngleAxis(_: PolarAngleAxisProps) {
  return null;
}

PolarAngleAxis.displayName = "PolarAngleAxis";

export function PolarRadiusAxis(_: PolarRadiusAxisProps) {
  return null;
}

PolarRadiusAxis.displayName = "PolarRadiusAxis";

export function Radar(_: RadarProps) {
  return null;
}

Radar.displayName = "Radar";

export function Tooltip() {
  return null;
}

Tooltip.displayName = "Tooltip";

export function RadarChart({ data, children }: RadarChartProps) {
  const childNodes = React.Children.toArray(children).filter(React.isValidElement) as React.ReactElement<any>[];
  const angleAxis = childNodes.find((child) => child.type === PolarAngleAxis);
  const radiusAxis = childNodes.find((child) => child.type === PolarRadiusAxis);
  const radar = childNodes.find((child) => child.type === Radar);

  const angleKey = angleAxis?.props.dataKey || "subject";
  const valueKey = radar?.props.dataKey || "value";
  const stroke = radar?.props.stroke || "#2563EB";
  const fill = radar?.props.fill || "#2563EB";
  const fillOpacity = radar?.props.fillOpacity ?? 0.25;
  const domain = radiusAxis?.props.domain || [0, 100];
  const maxDomain = Number(domain[1] || 100);
  const levels = [20, 40, 60, 80, 100];

  const points = data.map((item, index) => {
    const score = Number(item[valueKey] || 0);
    const { x, y } = vertex(index, data.length, (score / maxDomain) * MAX_R);
    return `${x},${y}`;
  });

  return (
    <svg viewBox="0 0 400 350" width="100%" height="100%">
      {levels.map((level) => {
        const polygon = data
          .map((_, index) => {
            const { x, y } = vertex(index, data.length, (level / maxDomain) * MAX_R);
            return `${x},${y}`;
          })
          .join(" ");
        return <polygon key={level} points={polygon} fill="none" stroke="#CBD5E1" strokeWidth="1" />;
      })}

      {data.map((_, index) => {
        const { x, y } = vertex(index, data.length, MAX_R);
        return <line key={`axis-${index}`} x1={CX} y1={CY} x2={x} y2={y} stroke="#E2E8F0" strokeWidth="1" />;
      })}

      <polygon points={points.join(" ")} fill={fill} fillOpacity={fillOpacity} stroke={stroke} strokeWidth="2" />

      {data.map((item, index) => {
        const label = String(item[angleKey] || "");
        const score = Number(item[valueKey] || 0);
        const point = vertex(index, data.length, (score / maxDomain) * MAX_R);
        const labelPoint = vertex(index, data.length, MAX_R + 24);
        return (
          <g key={label}>
            <circle cx={point.x} cy={point.y} r="4" fill={stroke} />
            <text x={labelPoint.x} y={labelPoint.y} textAnchor="middle" fontSize="12" fill="#334155">
              {label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
