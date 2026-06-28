import { NavLink } from 'react-router-dom';
import { useState, useEffect } from 'react';

function isMarketOpen() {
  const now = new Date();
  const ist = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
  const day = ist.getDay();
  if (day === 0 || day === 6) return false;
  const h = ist.getHours(), m = ist.getMinutes();
  const mins = h * 60 + m;
  return mins >= 555 && mins <= 930;
}

function ISTClock() {
  const [time, setTime] = useState('');
  useEffect(() => {
    const tick = () => {
      const t = new Date().toLocaleTimeString('en-IN', {
        timeZone: 'Asia/Kolkata',
        hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
      });
      setTime(t);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);
  return <span style={{ color: 'var(--text-muted)', fontSize: 12, fontVariantNumeric: 'tabular-nums' }}>{time} IST</span>;
}

const navStyle = ({ isActive }) => ({
  fontSize: 13,
  fontWeight: 500,
  color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
  padding: '4px 12px',
  borderRadius: 6,
  background: isActive ? 'var(--bg-elevated)' : 'transparent',
  transition: 'color 0.15s, background 0.15s',
  textDecoration: 'none',
});

export default function Navbar() {
  const open = isMarketOpen();
  return (
    <header style={{
      height: 56,
      display: 'flex',
      alignItems: 'center',
      padding: '0 24px',
      borderBottom: '1px solid var(--border-subtle)',
      background: 'var(--bg-card)',
      position: 'sticky',
      top: 0,
      zIndex: 100,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 160 }}>
        <img src="/logo.svg" alt="" width={28} height={28} />
        <span style={{ fontWeight: 700, fontSize: 15, letterSpacing: '0.04em', color: 'var(--text-primary)' }}>
          STOCKER
        </span>
      </div>

      <nav style={{ flex: 1, display: 'flex', justifyContent: 'center', gap: 4 }}>
        <NavLink to="/"          style={navStyle} end>Dashboard</NavLink>
        <NavLink to="/signals"   style={navStyle}>Signals</NavLink>
        <NavLink to="/portfolio" style={navStyle}>Portfolio</NavLink>
      </nav>

      <div style={{ display: 'flex', alignItems: 'center', gap: 16, minWidth: 160, justifyContent: 'flex-end' }}>
        <ISTClock />
        <span style={{
          fontSize: 11,
          fontWeight: 600,
          letterSpacing: '0.05em',
          padding: '3px 8px',
          borderRadius: 4,
          background: open ? 'var(--green-dim)' : 'var(--red-dim)',
          color: open ? 'var(--green)' : 'var(--red)',
          border: `1px solid ${open ? 'var(--green-border)' : 'var(--red-border)'}`,
        }}>
          {open ? 'OPEN' : 'CLOSED'}
        </span>
      </div>
    </header>
  );
}
