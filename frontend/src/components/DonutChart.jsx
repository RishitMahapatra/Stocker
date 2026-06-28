const RADIUS = 52;
const CIRC = 2 * Math.PI * RADIUS;

export default function DonutChart({ pct = 0, size = 140, label = 'Win Rate' }) {
  const clampedPct = Math.min(100, Math.max(0, pct));
  const fill = (clampedPct / 100) * CIRC;
  const gap  = CIRC - fill;
  const cx = size / 2;
  const cy = size / 2;
  const r = (size / 2) * 0.74;
  const circ = 2 * Math.PI * r;
  const strokeFill = (clampedPct / 100) * circ;

  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: 'rotate(-90deg)' }}>
        <circle
          cx={cx} cy={cy} r={r}
          fill="none"
          stroke="var(--track)"
          strokeWidth={size * 0.08}
        />
        <circle
          cx={cx} cy={cy} r={r}
          fill="none"
          stroke="var(--green)"
          strokeWidth={size * 0.08}
          strokeDasharray={`${strokeFill} ${circ - strokeFill}`}
          strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 0.8s ease-out' }}
        />
      </svg>
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
      }}>
        <span style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.06em', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
          {label}
        </span>
        <span style={{ fontSize: size * 0.22, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.1 }}>
          {clampedPct}%
        </span>
      </div>
    </div>
  );
}
