export default function KPICard({ label, value, icon, valueClass = '', gradientTop = false, children }) {
  return (
    <div className={`glass-card${gradientTop ? ' kpi-border-top' : ''}`} style={{
      borderRadius: 8, padding: 20,
      display: 'flex', flexDirection: 'column', gap: 8,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: '#bbcbb8' }}>
        <span style={{ fontSize: 12, fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase' }}>
          {label}
        </span>
        {icon && (
          <span className="material-symbols-outlined" style={{ fontSize: 20, color: '#bbcbb8' }}>{icon}</span>
        )}
      </div>
      <div className={valueClass} style={{ fontSize: 36, fontWeight: 700, letterSpacing: '-0.02em', lineHeight: '44px' }}>
        {value}
      </div>
      {children}
    </div>
  );
}
