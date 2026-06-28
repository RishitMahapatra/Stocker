export default function KPICard({ label, value, sub, children, accent = false }) {
  return (
    <div className="card" style={{
      display: 'flex',
      flexDirection: 'column',
      gap: 6,
      borderTop: accent ? '2px solid var(--green)' : '2px solid transparent',
    }}>
      <span style={{
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: '0.06em',
        textTransform: 'uppercase',
        color: 'var(--text-muted)',
      }}>{label}</span>
      <span style={{
        fontSize: 28,
        fontWeight: 700,
        letterSpacing: '-0.02em',
        lineHeight: 1.1,
        color: 'var(--text-primary)',
      }}>{value}</span>
      {sub && (
        <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{sub}</span>
      )}
      {children}
    </div>
  );
}
