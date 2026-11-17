import { useRef } from "react";

const WIDTH = 720;
const HEIGHT = 310;
const MARGIN = { top: 20, right: 20, bottom: 66, left: 72 };
const FACTORS = {
  temperature: { field: "T2M", label: "Temperature", color: "#ff5b61", unit: "Hz", axis: "Frequency (Hz)" },
  rainfall: { field: "PRECTOTCORR", label: "Rainfall", color: "#77b9ff", unit: "mm/day", axis: "Rainfall (mm/day)" },
  wind: { field: "WS2M", label: "Wind", color: "#a8b0b8", unit: "m/s", axis: "Wind speed (m/s)" },
  humidity: { field: "RH2M", label: "Humidity", color: "#d5a5ff", unit: "%", axis: "Humidity (%)" },
};
const ALL_FACTORS = Object.keys(FACTORS);
const TREND_THRESHOLDS = { temperature: 0.3, rainfall: 0.1, wind: 0.1, humidity: 1 };

function monthLabel(value) {
  const [year, month] = value.split("-").map(Number);
  const label = new Date(Date.UTC(year, month - 1, 1))
    .toLocaleString("en", { month: "short", timeZone: "UTC" });
  return month === 1 || month === 12 ? `${label} '${String(year).slice(-2)}` : label;
}

function getSeries(points, selectedFactors) {
  const factors = selectedFactors.length ? selectedFactors : ALL_FACTORS;
  const combined = factors.length > 1;
  return factors.map((id) => {
    const factor = FACTORS[id];
    const values = points.map((point) => {
      const raw = point[factor.field];
      if (raw == null) return null;
      if (combined) {
        if (id === "temperature") {
          const normalized = Math.max(0, Math.min(1, (raw + 30) / 70));
          return (2 ** (normalized * 2.5) - 1) / (2 ** 2.5 - 1);
        }
        if (id === "rainfall") return Math.max(0, Math.min(1, Math.log1p(Math.max(0, raw)) / Math.log1p(50)));
        if (id === "wind") return Math.max(0, Math.min(1, raw / 20));
        return Math.max(0, Math.min(1, raw / 100));
      }
      if (id === "temperature") {
        const normalized = Math.max(0, Math.min(1, (raw + 30) / 70));
        return 110 * 2 ** (normalized * 2.5);
      }
      return raw;
    });
    return { ...factor, id, values, rawValues: points.map((point) => point[factor.field]) };
  });
}

function getTrend(item) {
  const values = item.rawValues.filter(Number.isFinite);
  if (values.length < 2) return "has too little data for a trend";
  const windowSize = Math.min(3, Math.floor(values.length / 2));
  const average = (samples) => samples.reduce((sum, value) => sum + value, 0) / samples.length;
  const initialAverage = average(values.slice(0, windowSize));
  const recentAverage = average(values.slice(-windowSize));
  const threshold = Math.max(TREND_THRESHOLDS[item.id], Math.abs(initialAverage) * 0.03);
  if (recentAverage - initialAverage > threshold) return "increased over the past year";
  if (initialAverage - recentAverage > threshold) return "decreased over the past year";
  return "remained mostly steady over the past year";
}

function getStoryTrend(item) {
  const trend = getTrend(item);
  if (trend === "increased over the past year") return "has been trending upward";
  if (trend === "decreased over the past year") return "has been trending downward";
  if (trend === "remained mostly steady over the past year") return "has remained mostly steady";
  return "does not yet have enough observations to show a clear trend";
}

export function createClimateStory(points, selectedFactors = []) {
  if (!points?.length) return "There is not enough climate data to tell this story yet.";
  const series = getSeries(points, selectedFactors);
  const observations = series.map((item) =>
    `${item.label.toLowerCase()} ${getStoryTrend(item)}`);
  const opening = `As the year unfolds, ${observations[0]}.`;
  if (observations.length === 1) {
    return `${opening} This is one part of the climate rhythm here.`;
  }
  const laterObservations = observations.slice(1);
  const joinedObservations = laterObservations.length === 1
    ? laterObservations[0]
    : `${laterObservations.slice(0, -1).join(", ")}, and ${laterObservations.at(-1)}`;
  return `${opening} Meanwhile, ${joinedObservations}. Together, these patterns create the climate rhythm of this place.`;
}

function smoothPath(values, xAt, yAt) {
  const segments = [];
  let segment = [];
  values.forEach((value, index) => {
    if (value == null) {
      if (segment.length) segments.push(segment);
      segment = [];
    } else segment.push({ x: xAt(index), y: yAt(value) });
  });
  if (segment.length) segments.push(segment);
  return segments.map((points) => {
    if (points.length === 1) return `M ${points[0].x} ${points[0].y}`;
    let path = `M ${points[0].x} ${points[0].y}`;
    for (let index = 0; index < points.length - 1; index += 1) {
      const previous = points[Math.max(0, index - 1)];
      const current = points[index];
      const next = points[index + 1];
      const following = points[Math.min(points.length - 1, index + 2)];
      path += ` C ${current.x + (next.x - previous.x) / 6} ${current.y + (next.y - previous.y) / 6}`
        + ` ${next.x - (following.x - current.x) / 6} ${next.y - (following.y - current.y) / 6}`
        + ` ${next.x} ${next.y}`;
    }
    return path;
  }).join(" ");
}

export default function ClimateFactorChart({ points, selectedFactors = [], currentTime = 0, duration = 0 }) {
  const dialogRef = useRef(null);
  if (!points?.length) return null;
  const series = getSeries(points, selectedFactors);
  const combined = series.length > 1;
  const plottedValues = series.flatMap((item) => item.values.filter((value) => value != null));
  if (!plottedValues.length) return null;
  let min = combined ? 0 : Math.floor(Math.min(...plottedValues) / 10) * 10;
  let max = combined ? 1 : Math.ceil(Math.max(...plottedValues) / 10) * 10;
  if (max <= min) max = min + 1;
  if (!combined) {
    const padding = (max - min) * 0.08;
    min = Math.max(0, min - padding);
    max += padding;
  }
  const span = max - min;
  const plotWidth = WIDTH - MARGIN.left - MARGIN.right;
  const plotHeight = HEIGHT - MARGIN.top - MARGIN.bottom;
  const xAt = (index) => MARGIN.left + (points.length === 1 ? 0 : index / (points.length - 1)) * plotWidth;
  const yAt = (value) => MARGIN.top + (max - value) / span * plotHeight;
  const tickCount = 4;
  const progress = duration > 0 ? Math.max(0, Math.min(1, currentTime / duration)) : 0;
  const playheadX = MARGIN.left + progress * plotWidth;
  const monthTickIndexes = [...new Set([0, Math.round((points.length - 1) / 2), points.length - 1])];
  const axisLabel = combined ? "Relative sound mapping (0-1)" : series[0].axis;
  const insights = <div className="climate-insights" aria-label="Climate trends">
    {series.map((item) => <span className="climate-insight" key={item.id}
      style={{ "--factor-color": item.color }}>
      <i aria-hidden="true" />
      {item.label} {getTrend(item)}
    </span>)}
  </div>;

  const graph = <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img"
    aria-label={`${combined ? "Combined climate factors" : series[0].label} by month synchronized to playback`}>
    {[...Array(tickCount + 1)].map((_, index) => {
      const value = min + span * index / tickCount;
      const y = yAt(value);
      return <g key={index}>
        <line className="chart-grid" x1={MARGIN.left} x2={WIDTH - MARGIN.right} y1={y} y2={y} />
        <text className="chart-tick" x={MARGIN.left - 9} y={y + 4} textAnchor="end">
          {combined ? value.toFixed(2) : value.toFixed(value < 10 ? 1 : 0)}
        </text>
      </g>;
    })}
    <line className="chart-axis" x1={MARGIN.left} x2={MARGIN.left} y1={MARGIN.top} y2={HEIGHT - MARGIN.bottom} />
    <line className="chart-axis" x1={MARGIN.left} x2={WIDTH - MARGIN.right} y1={HEIGHT - MARGIN.bottom} y2={HEIGHT - MARGIN.bottom} />
    {series.map((item) => <g key={item.id}>
      <path className="chart-line" d={smoothPath(item.values, xAt, yAt)} style={{ stroke: item.color }} />
      {item.values.map((value, index) => value == null ? null : <circle key={points[index].month}
        className="chart-point" style={{ fill: item.color }} cx={xAt(index)} cy={yAt(value)} r="4">
        <title>{monthLabel(points[index].month)}: {item.rawValues[index]} {item.id === "temperature" ? "degrees C" : item.unit}
          {item.id === "temperature" && !combined ? ` -> ${value.toFixed(1)} Hz` : ""}</title>
      </circle>)}
    </g>)}
    <line className="chart-playhead" x1={playheadX} x2={playheadX}
      y1={MARGIN.top} y2={HEIGHT - MARGIN.bottom} />
    {points.map((point, index) => monthTickIndexes.includes(index) && <text key={point.month}
      className="chart-tick" x={xAt(index)} y={HEIGHT - MARGIN.bottom + 20} textAnchor="middle">
      {monthLabel(point.month)}
    </text>)}
    <text className="chart-axis-label" transform={`translate(16 ${MARGIN.top + plotHeight / 2}) rotate(-90)`}
      textAnchor="middle">{axisLabel}</text>
    <text className="chart-axis-label" x={MARGIN.left + plotWidth / 2} y={HEIGHT - 6}
      textAnchor="middle">Month</text>
  </svg>;

  return <section className="temperature-chart" aria-label="Climate graph">
    {insights}
    <button type="button" className="chart-expand-trigger" aria-haspopup="dialog"
      aria-label="Open enlarged climate graph" onClick={() => dialogRef.current?.showModal()}>
      {graph}
    </button>
    <dialog ref={dialogRef} className="chart-expanded-dialog" aria-label="Expanded climate graph"
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          event.preventDefault();
          event.currentTarget.close();
        }
      }}
      onClick={(event) => {
        if (event.target === event.currentTarget) event.currentTarget.close();
      }}>
      <button type="button" className="chart-close-button" aria-label="Close enlarged climate graph"
        onClick={() => dialogRef.current?.close()}>Close</button>
      {graph}
    </dialog>
  </section>;
}
