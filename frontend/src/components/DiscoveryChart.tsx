import React from 'react';
import { BarChart3, ScatterChart as ScatterIcon, LineChart as LineIcon } from 'lucide-react';
import type { VisualizationSpec } from '../api/types';

interface DiscoveryChartProps {
  spec?: VisualizationSpec | null;
}

export const DiscoveryChart: React.FC<DiscoveryChartProps> = ({ spec }) => {
  if (!spec || !spec.data || !Array.isArray(spec.data) || spec.data.length === 0) {
    return null;
  }

  const { chart_type, title, x_label, y_label, x_key, y_key, data } = spec;

  const width = 560;
  const height = 230;
  const padLeft = 60;
  const padRight = 30;
  const padTop = 28;
  const padBottom = 48;
  const plotWidth = width - padLeft - padRight;
  const plotHeight = height - padTop - padBottom;

  const getChartIcon = () => {
    switch (chart_type) {
      case 'scatter':
        return <ScatterIcon className="h-3.5 w-3.5 text-sky-500" />;
      case 'line':
        return <LineIcon className="h-3.5 w-3.5 text-indigo-500" />;
      default:
        return <BarChart3 className="h-3.5 w-3.5 text-indigo-500" />;
    }
  };

  // Render Scatter
  const renderScatter = () => {
    const validPoints = data
      .map((d) => ({ x: Number(d[x_key]), y: Number(d[y_key]) }))
      .filter((d) => !isNaN(d.x) && !isNaN(d.y));

    if (validPoints.length === 0) return null;

    let minX = Math.min(...validPoints.map((d) => d.x));
    let maxX = Math.max(...validPoints.map((d) => d.x));
    let minY = Math.min(...validPoints.map((d) => d.y));
    let maxY = Math.max(...validPoints.map((d) => d.y));

    if (minX === maxX) { minX -= 1; maxX += 1; }
    if (minY === maxY) { minY -= 1; maxY += 1; }

    const padX = (maxX - minX) * 0.06;
    const padY = (maxY - minY) * 0.06;
    minX -= padX; maxX += padX;
    minY -= padY; maxY += padY;

    const gridLines = [];
    for (let i = 0; i <= 3; i++) {
      const frac = i / 3;
      const gy = padTop + plotHeight - frac * plotHeight;
      const valY = minY + frac * (maxY - minY);
      gridLines.push(
        <g key={`y-${i}`}>
          <line
            x1={padLeft}
            y1={gy}
            x2={padLeft + plotWidth}
            y2={gy}
            stroke="currentColor"
            strokeDasharray="3,3"
            className="text-zinc-200"
          />
          <text
            x={padLeft - 8}
            y={gy + 4}
            textAnchor="end"
            fontSize="10"
            className="fill-zinc-400 font-mono"
          >
            {valY >= 100 ? Math.round(valY) : valY.toFixed(1)}
          </text>
        </g>
      );

      const gx = padLeft + frac * plotWidth;
      const valX = minX + frac * (maxX - minX);
      gridLines.push(
        <g key={`x-${i}`}>
          <line
            x1={gx}
            y1={padTop}
            x2={gx}
            y2={padTop + plotHeight}
            stroke="currentColor"
            strokeDasharray="3,3"
            className="text-zinc-200"
          />
          <text
            x={gx}
            y={padTop + plotHeight + 16}
            textAnchor="middle"
            fontSize="10"
            className="fill-zinc-400 font-mono"
          >
            {valX >= 100 ? Math.round(valX) : valX.toFixed(1)}
          </text>
        </g>
      );
    }

    const circles = validPoints.map((p, idx) => {
      const cx = padLeft + ((p.x - minX) / (maxX - minX)) * plotWidth;
      const cy = padTop + plotHeight - ((p.y - minY) / (maxY - minY)) * plotHeight;
      return (
        <circle
          key={idx}
          cx={cx}
          cy={cy}
          r="3.2"
          className="fill-sky-500 opacity-80 hover:opacity-100 hover:r-4 transition-all"
        >
          <title>{`${x_label}: ${p.x}, ${y_label}: ${p.y}`}</title>
        </circle>
      );
    });

    return (
      <>
        {gridLines}
        {circles}
      </>
    );
  };

  // Render Bar
  const renderBar = () => {
    const items = data
      .map((d) => ({
        cat: String(d[x_key] ?? ''),
        val: Number(d[y_key] ?? 0),
      }))
      .filter((d) => !isNaN(d.val));

    if (items.length === 0) return null;

    let minY = Math.min(0, Math.min(...items.map((d) => d.val)));
    let maxY = Math.max(0, Math.max(...items.map((d) => d.val)));
    if (minY === maxY) { maxY += 1; }
    maxY = maxY * 1.18;

    const gridLines = [];
    for (let i = 0; i <= 3; i++) {
      const frac = i / 3;
      const gy = padTop + plotHeight - frac * plotHeight;
      const valY = minY + frac * (maxY - minY);
      gridLines.push(
        <g key={`y-${i}`}>
          <line
            x1={padLeft}
            y1={gy}
            x2={padLeft + plotWidth}
            y2={gy}
            stroke="currentColor"
            strokeDasharray="3,3"
            className="text-zinc-200"
          />
          <text
            x={padLeft - 8}
            y={gy + 4}
            textAnchor="end"
            fontSize="10"
            className="fill-zinc-400 font-mono"
          >
            {valY >= 100 ? Math.round(valY) : valY.toFixed(1)}
          </text>
        </g>
      );
    }

    const baseY = padTop + plotHeight - ((0 - minY) / (maxY - minY)) * plotHeight;
    gridLines.push(
      <line
        key="base"
        x1={padLeft}
        y1={baseY}
        x2={padLeft + plotWidth}
        y2={baseY}
        stroke="currentColor"
        strokeWidth="1.2"
        className="text-zinc-300"
      />
    );

    const n = items.length;
    const slotWidth = plotWidth / n;
    const barWidth = Math.min(46, Math.max(14, slotWidth * 0.65));

    const bars = items.map((item, i) => {
      const barX = padLeft + i * slotWidth + (slotWidth - barWidth) / 2;
      const valY = padTop + plotHeight - ((item.val - minY) / (maxY - minY)) * plotHeight;
      const barY = Math.min(baseY, valY);
      const barH = Math.max(2, Math.abs(baseY - valY));
      const labelY = item.val >= 0 ? barY - 5 : barY + barH + 12;
      const catLabel = item.cat.length > 9 ? item.cat.slice(0, 8) + '…' : item.cat;

      return (
        <g key={i}>
          <rect
            x={barX}
            y={barY}
            width={barWidth}
            height={barH}
            rx="3"
            className="fill-indigo-600 hover:fill-indigo-500 transition-colors"
          >
            <title>{`${item.cat}: ${item.val}`}</title>
          </rect>
          <text
            x={barX + barWidth / 2}
            y={labelY}
            textAnchor="middle"
            fontSize="10.5"
            fontWeight="600"
            className="fill-zinc-700 font-mono"
          >
            {item.val}
          </text>
          <text
            x={barX + barWidth / 2}
            y={padTop + plotHeight + 17}
            textAnchor="middle"
            fontSize="10"
            className="fill-zinc-500"
          >
            {catLabel}
          </text>
        </g>
      );
    });

    return (
      <>
        {gridLines}
        {bars}
      </>
    );
  };

  // Render Line
  const renderLine = () => {
    const items = data
      .map((d) => ({
        label: String(d[x_key] ?? ''),
        val: Number(d[y_key] ?? 0),
      }))
      .filter((d) => !isNaN(d.val));

    if (items.length === 0) return null;

    let minY = Math.min(...items.map((d) => d.val));
    let maxY = Math.max(...items.map((d) => d.val));
    if (minY === maxY) { minY -= 1; maxY += 1; }
    const padY = (maxY - minY) * 0.12;
    minY -= padY; maxY += padY;

    const gridLines = [];
    for (let i = 0; i <= 3; i++) {
      const frac = i / 3;
      const gy = padTop + plotHeight - frac * plotHeight;
      const valY = minY + frac * (maxY - minY);
      gridLines.push(
        <g key={`y-${i}`}>
          <line
            x1={padLeft}
            y1={gy}
            x2={padLeft + plotWidth}
            y2={gy}
            stroke="currentColor"
            strokeDasharray="3,3"
            className="text-zinc-200"
          />
          <text
            x={padLeft - 8}
            y={gy + 4}
            textAnchor="end"
            fontSize="10"
            className="fill-zinc-400 font-mono"
          >
            {valY >= 100 ? Math.round(valY) : valY.toFixed(1)}
          </text>
        </g>
      );
    }

    const n = items.length;
    const coords = items.map((item, i) => {
      const cx = padLeft + (n === 1 ? plotWidth / 2 : (i / (n - 1)) * plotWidth);
      const cy = padTop + plotHeight - ((item.val - minY) / (maxY - minY)) * plotHeight;
      return { x: cx, y: cy, label: item.label, val: item.val };
    });

    const first = coords[0];
    const last = coords[coords.length - 1];
    const bottomY = padTop + plotHeight;
    let areaD = `M ${first.x} ${bottomY} L ${first.x} ${first.y}`;
    for (let i = 1; i < coords.length; i++) {
      areaD += ` L ${coords[i].x} ${coords[i].y}`;
    }
    areaD += ` L ${last.x} ${bottomY} Z`;

    let lineD = `M ${first.x} ${first.y}`;
    for (let i = 1; i < coords.length; i++) {
      lineD += ` L ${coords[i].x} ${coords[i].y}`;
    }

    const points = coords.map((pt, idx) => {
      const segLabel = pt.label.length > 7 ? pt.label.slice(0, 6) + '…' : pt.label;
      return (
        <g key={idx}>
          <circle
            cx={pt.x}
            cy={pt.y}
            r="3.8"
            className="fill-indigo-600 stroke-white stroke-2"
          >
            <title>{`${pt.label}: ${pt.val}`}</title>
          </circle>
          {coords.length <= 12 && (
            <>
              <text
                x={pt.x}
                y={pt.y - 7}
                textAnchor="middle"
                fontSize="10"
                fontWeight="600"
                className="fill-zinc-700 font-mono"
              >
                {pt.val}
              </text>
              <text
                x={pt.x}
                y={padTop + plotHeight + 17}
                textAnchor="middle"
                fontSize="10"
                className="fill-zinc-500"
              >
                {segLabel}
              </text>
            </>
          )}
        </g>
      );
    });

    return (
      <>
        {gridLines}
        <path d={areaD} className="fill-indigo-50/60" />
        <path
          d={lineD}
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="text-indigo-600"
        />
        {points}
      </>
    );
  };

  return (
    <div className="rounded-xl border border-zinc-200/90 bg-zinc-50/70 p-3.5 my-3.5 shadow-2xs">
      <div className="flex items-center justify-between mb-2 px-1">
        <div className="flex items-center space-x-1.5 text-xs font-semibold text-zinc-800">
          {getChartIcon()}
          <span>{title}</span>
        </div>
        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200/60">
          {chart_type}
        </span>
      </div>

      <div className="w-full overflow-hidden">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto max-h-56 block"
          preserveAspectRatio="xMidYMid meet"
        >
          {chart_type === 'scatter' && renderScatter()}
          {chart_type === 'bar' && renderBar()}
          {chart_type === 'line' && renderLine()}

          {/* Axis Labels */}
          <text
            x={padLeft + plotWidth / 2}
            y={height - 8}
            textAnchor="middle"
            fontSize="10.5"
            fontWeight="600"
            className="fill-zinc-500"
          >
            {x_label}
          </text>
          <text
            x={14}
            y={padTop + plotHeight / 2}
            textAnchor="middle"
            fontSize="10.5"
            fontWeight="600"
            className="fill-zinc-500"
            transform={`rotate(-90 14 ${padTop + plotHeight / 2})`}
          >
            {y_label}
          </text>
        </svg>
      </div>
    </div>
  );
};
