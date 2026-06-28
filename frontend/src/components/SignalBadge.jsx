export default function SignalBadge({ signal, size = 'md' }) {
  const s = (signal || 'HOLD').toUpperCase();
  const cls = s === 'BUY' ? 'badge-buy' : s === 'SELL' ? 'badge-sell' : 'badge-hold';
  const prefix = s === 'BUY' ? '↗' : s === 'SELL' ? '↘' : '—';
  const pad = size === 'sm' ? '2px 7px' : '3px 10px';
  const fs  = size === 'sm' ? 10 : 11;

  return (
    <span className={cls} style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 4,
      borderRadius: 4,
      padding: pad,
      fontSize: fs,
      fontWeight: 700,
      letterSpacing: '0.05em',
      whiteSpace: 'nowrap',
    }}>
      <span style={{ fontSize: fs + 1 }}>{prefix}</span>
      {s}
    </span>
  );
}
