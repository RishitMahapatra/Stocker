import { NavLink } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchHealth } from '../api/endpoints';

function isMarketOpen() {
  const now = new Date();
  // Convert to IST (UTC+5:30)
  const ist = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
  const day = ist.getDay(); // 0=Sun,6=Sat
  if (day === 0 || day === 6) return false;
  const h = ist.getHours(), m = ist.getMinutes();
  const mins = h * 60 + m;
  return mins >= 555 && mins <= 930; // 9:15–15:30
}

export default function Navbar() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: 60000,
    retry: false,
  });

  const open = health ? isMarketOpen() : false;

  const linkStyle = ({ isActive }) => ({
    fontSize: '12px', fontWeight: 600, letterSpacing: '0.05em',
    color: isActive ? '#3fe56c' : '#bbcbb8',
    borderBottom: isActive ? '2px solid #3fe56c' : '2px solid transparent',
    paddingBottom: '4px',
    transition: 'color 0.15s',
    textDecoration: 'none',
  });

  return (
    <nav style={{
      background: '#0b141c',
      borderBottom: '1px solid #3c4a3c',
      boxShadow: '0 1px 0 rgba(63,229,108,0.12), 0 4px 24px rgba(0,0,0,0.4)',
      position: 'sticky', top: 0, zIndex: 50,
    }}>
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        width: '100%', padding: '16px 24px', maxWidth: '100%',
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: 22, fontWeight: 700, color: '#dae3ee', letterSpacing: '-0.01em' }}>
              STOCKER
            </span>
            <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.05em', color: '#bbcbb8' }}>
              Watch • Analyze • Decide
            </span>
          </div>
        </div>

        {/* Nav links */}
        <div style={{ display: 'flex', gap: 32 }}>
          <NavLink to="/"          style={linkStyle}>Dashboard</NavLink>
          <NavLink to="/signals"   style={linkStyle}>Signals</NavLink>
          <NavLink to="/portfolio" style={linkStyle}>Portfolio</NavLink>
        </div>

        {/* Market status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div className={open ? 'market-pill' : 'market-pill'} style={
            !open ? { background: 'rgba(255,61,0,0.08)', borderColor: 'rgba(255,61,0,0.25)' } : {}
          }>
            <span className="pulse-dot" style={!open ? { background: '#FF3D00' } : {}} />
            {open ? 'Market Open' : 'Market Closed'}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#bbcbb8', fontSize: 12, fontWeight: 600 }}>
            <span className="material-symbols-outlined" style={{ fontSize: 14 }}>schedule</span>
            {new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Kolkata' })} IST
          </div>
        </div>
      </div>
    </nav>
  );
}
