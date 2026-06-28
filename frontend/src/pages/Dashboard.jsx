import { useQuery } from '@tanstack/react-query';
import { fetchSignals, fetchPortfolio } from '../api/endpoints';
import SignalBadge from '../components/SignalBadge';
import ScoreBar from '../components/ScoreBar';
import KPICard from '../components/KPICard';

const fmtINR = (n) =>
  n == null ? '—' : new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);

const fmtPrice = (n) =>
  n == null ? '—' : '₹' + new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 }).format(n);

function SkeletonRow() {
  return (
    <tr style={{ borderBottom: '1px solid #21262D' }}>
      {[...Array(6)].map((_, i) => (
        <td key={i} style={{ padding: 20 }}>
          <div className="skeleton" style={{ height: 14, width: i === 0 ? 80 : 60 }} />
        </td>
      ))}
    </tr>
  );
}

export default function Dashboard() {
  const { data: signals, isLoading: sigLoading, error: sigError } = useQuery({
    queryKey: ['signals'],
    queryFn: fetchSignals,
    refetchInterval: 30000,
  });

  const { data: portfolio, isLoading: portLoading } = useQuery({
    queryKey: ['portfolio'],
    queryFn: fetchPortfolio,
    refetchInterval: 30000,
  });

  const buyCount   = (signals || []).filter(s => s.signal === 'BUY').length;
  const totalPnl   = portfolio?.total_pnl ?? null;
  const winRate    = portfolio?.win_rate ?? null;
  const deployed   = portfolio?.deployed_pct ?? null;

  return (
    <main style={{ padding: 24, maxWidth: 1280, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 32 }}
          className="fade-in">

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16 }}>
        <KPICard
          label="Total Signals Today"
          value={sigLoading ? '—' : (signals?.length ?? 0)}
          icon="bolt"
          className="delay-1"
        />
        <KPICard
          label="BUY Signals"
          value={sigLoading ? '—' : buyCount}
          icon="arrow_upward"
          valueClass="glow-green"
          gradientTop
          className="delay-2"
        />
        <KPICard
          label="Portfolio P&L"
          value={portLoading ? '—' : (totalPnl != null ? (totalPnl >= 0 ? '+' : '') + fmtINR(totalPnl) : '—')}
          icon="currency_rupee"
          valueClass={totalPnl != null && totalPnl >= 0 ? 'glow-green' : 'glow-red'}
          className="delay-3"
        >
          {totalPnl != null && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#00C853', fontSize: 12, fontWeight: 600 }}>
              <span className="material-symbols-outlined" style={{ fontSize: 14 }}>trending_up</span>
              {portfolio?.open_positions ?? 0} open positions
            </div>
          )}
        </KPICard>
        <KPICard
          label="Win Rate"
          value={portLoading ? '—' : (winRate != null ? `${Math.round(winRate)}%` : '—')}
          icon="emoji_events"
          valueClass="glow-win"
          className="delay-4"
        >
          <div className="score-track" style={{ marginTop: 4 }}>
            <ScoreBar score={winRate ?? 0} color="#e5a000" showNumber={false} />
          </div>
        </KPICard>
      </div>

      {/* Main content row */}
      <div style={{ display: 'flex', gap: 32, flexWrap: 'wrap' }}>

        {/* Live Signals Table */}
        <div className="glass-card" style={{ flex: '1 1 600px', borderRadius: 8, overflow: 'hidden' }}>
          <div style={{
            padding: '16px 20px', borderBottom: '1px solid #21262D',
            background: '#161B22', display: 'flex', alignItems: 'center', gap: 8,
          }}>
            <span className="pulse-dot" />
            <h2 style={{ fontSize: 22, fontWeight: 600 }}>Live Signals</h2>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead style={{ background: '#161B22', borderBottom: '1px solid #21262D' }}>
                <tr>
                  {['Ticker','Price','Score','Signal','Agents','Updated'].map(h => (
                    <th key={h} style={{ padding: '12px 20px', fontSize: 12, fontWeight: 600, letterSpacing: '0.05em', color: '#bbcbb8' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sigLoading && [...Array(4)].map((_, i) => <SkeletonRow key={i} />)}
                {sigError && (
                  <tr><td colSpan={6} style={{ padding: 32, textAlign: 'center', color: '#bbcbb8' }}>
                    Error loading signals. Is the backend running?
                  </td></tr>
                )}
                {!sigLoading && !sigError && (!signals || signals.length === 0) && (
                  <tr><td colSpan={6} style={{ padding: 32, textAlign: 'center', color: '#bbcbb8' }}>
                    No data yet — run the pipeline first.
                  </td></tr>
                )}
                {(signals || []).map((row, i) => (
                  <tr key={row.ticker} className={`table-row delay-${Math.min(i+1,4)}`}
                      style={{ borderBottom: '1px solid #21262D', cursor: 'pointer', animation: `fadeInUp 0.4s ease ${i*0.06}s both` }}>
                    <td style={{ padding: 20, fontSize: 12, fontWeight: 600 }}>{row.ticker}</td>
                    <td style={{ padding: 20, fontSize: 14 }}>{fmtPrice(row.current_price)}</td>
                    <td style={{ padding: 20 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, width: 96 }}>
                        <span style={{ fontSize: 12, fontWeight: 600, color: row.composite_score >= 60 ? '#00C853' : row.composite_score <= 40 ? '#FF3D00' : '#ffbd45' }}>
                          {row.composite_score ?? '—'}
                        </span>
                        <ScoreBar score={row.composite_score ?? 0} showNumber={false} />
                      </div>
                    </td>
                    <td style={{ padding: 20 }}><SignalBadge signal={row.signal} size="sm" /></td>
                    <td style={{ padding: 20 }}>
                      <div style={{ display: 'flex', gap: 4 }}>
                        {['technical_score','sentiment_score','fundamental_score'].map((k, j) => {
                          const v = row[k];
                          const c = v >= 60 ? '#00C853' : v <= 40 ? '#FF3D00' : '#2d363e';
                          return <div key={j} title={k} style={{ width: 8, height: 8, borderRadius: '50%', background: c }} />;
                        })}
                      </div>
                    </td>
                    <td style={{ padding: 20, textAlign: 'right', fontSize: 14, color: '#bbcbb8' }}>
                      {row.decided_at ? new Date(row.decided_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Portfolio Snapshot */}
        <div style={{ flex: '0 0 300px', display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Donut */}
          <div className="glass-card" style={{ borderRadius: 8, padding: 20 }}>
            <h2 style={{ fontSize: 22, fontWeight: 600, marginBottom: 16 }}>Portfolio Snapshot</h2>
            <div style={{ display: 'flex', justifyContent: 'center', padding: '16px 0' }}>
              {portLoading ? (
                <div className="skeleton" style={{ width: 192, height: 192, borderRadius: '50%' }} />
              ) : (
                <div className="donut-glow" style={{ position: 'relative', width: 192, height: 192 }}>
                  <svg width="192" height="192" viewBox="0 0 36 36" style={{ transform: 'rotate(-90deg)' }}>
                    <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                          fill="none" stroke="#2d363e" strokeWidth="3" />
                    <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                          fill="none" stroke="#00c853"
                          strokeWidth="3"
                          strokeDasharray={`${(deployed ?? 12)}, 100`} />
                  </svg>
                  <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                    <span style={{ fontSize: 11, fontWeight: 600, color: '#bbcbb8', textTransform: 'uppercase' }}>Deployed</span>
                    <span className="glow-green" style={{ fontSize: 28, fontWeight: 700, color: '#00c853' }}>
                      {deployed != null ? `${Math.round(deployed * 100)}%` : '12%'}
                    </span>
                  </div>
                </div>
              )}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, paddingTop: 8, borderTop: '1px solid #21262D', marginTop: 4 }}>
              <div style={{ width: 12, height: 12, borderRadius: 2, background: '#2d363e' }} />
              <span style={{ fontSize: 12, fontWeight: 600, color: '#bbcbb8' }}>
                Available: {deployed != null ? `${Math.round((1 - deployed) * 100)}%` : '88%'}
              </span>
            </div>
          </div>

          {/* Open positions mini */}
          <div className="glass-card" style={{ borderRadius: 8, padding: 20 }}>
            <h3 style={{ fontSize: 12, fontWeight: 600, letterSpacing: '0.05em', color: '#bbcbb8', textTransform: 'uppercase', marginBottom: 12 }}>
              Open Positions
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {portLoading && [...Array(2)].map((_, i) => (
                <div key={i} className="skeleton" style={{ height: 56, borderRadius: 4 }} />
              ))}
              {!portLoading && portfolio?.open_positions === 0 && (
                <p style={{ fontSize: 14, color: '#bbcbb8', textAlign: 'center', padding: '8px 0' }}>
                  No open positions
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
