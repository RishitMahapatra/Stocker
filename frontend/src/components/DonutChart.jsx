export default function DonutChart({ pct = 0, size = 192, label = 'Win Ratio' }) {
  // pct = win%, remainder shown as loss
  const lossPct = Math.max(0, 100 - pct - 17); // ~17% loss portion shown in red
  const neutralPct = Math.max(0, 100 - pct - lossPct);

  const conicStyle = {
    background: `conic-gradient(from 180deg, #3fe56c 0% ${pct}%, #ffb4ab ${pct}% ${pct + 17}%, #2d363e ${pct + 17}% 100%)`,
    width: size, height: size, borderRadius: '50%',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    position: 'relative',
  };

  return (
    <div className="donut-glow" style={conicStyle}>
      <div style={{
        position: 'absolute',
        inset: 8,
        background: '#182028',
        borderRadius: '50%',
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      }}>
        <span style={{ fontSize: 12, fontWeight: 600, letterSpacing: '0.05em', color: '#bbcbb8', textTransform: 'uppercase' }}>
          {label}
        </span>
        <span style={{ fontSize: 32, fontWeight: 700, color: '#dae3ee', lineHeight: 1, marginTop: 4 }}>
          {pct}%
        </span>
      </div>
    </div>
  );
}
