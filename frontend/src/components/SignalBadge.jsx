export default function SignalBadge({ signal, size = 'md' }) {
  const s = (signal || '').toUpperCase();
  const cls = s === 'BUY' ? 'signal-buy' : s === 'SELL' ? 'signal-sell' : 'signal-hold';
  const icon = s === 'BUY' ? 'trending_up' : s === 'SELL' ? 'trending_down' : 'horizontal_rule';
  const pad = size === 'sm' ? '2px 8px' : '4px 12px';
  const fs  = size === 'sm' ? 10 : 12;

  return (
    <span className={cls} style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      borderRadius: 9999, padding: pad,
      fontSize: fs, fontWeight: 600, letterSpacing: '0.05em',
      whiteSpace: 'nowrap',
    }}>
      <span className="material-symbols-outlined" style={{ fontSize: 14 }}>{icon}</span>
      {s || 'HOLD'}
    </span>
  );
}
