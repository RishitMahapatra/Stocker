import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { fetchSignals, fetchPortfolio } from '../api/endpoints';
import SignalBadge from '../components/SignalBadge';
import ScoreBar from '../components/ScoreBar';
import KPICard from '../components/KPICard';
import DonutChart from '../components/DonutChart';

const fmtINR = (n, sign = false) => {
  if (n == null) return '—';
  const abs = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Math.abs(n));
  if (sign && n > 0) return '+' + abs;
  if (n < 0) return '-' + abs;
  return abs;
};

const fmtPrice = (n) =>
  n == null ? '—' : '₹' + new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 }).format(n);

const pnlColor = (n) => n == null ? 'inherit' : n > 0 ? 'var(--green)' : n < 0 ? 'var(--red)' : 'inherit';

export default function Dashboard() {
  const navigate = useNavigate();

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

  const buyCount  = (signals || []).filter(s => s.signal === 'BUY').length;
  const totalPnl  = portfolio?.total_pnl ?? null;
  const winRate   = portfolio?.win_rate != null ? Math.round(portfolio.win_rate) : null;
  const deployed  = portfolio?.deployed_pct != null ? Math.round(portfolio.deployed_pct * 100) : null;

  return (
    <main className="page-enter" style={{ padding: '24px', maxWidth: 1280, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* KPI row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12 }}>
        <KPICard label="Total Signals" value={sigLoading ? '—' : (signals?.length ?? 0)} />
        <KPICard label="BUY Signals"   value={sigLoading ? '—' : buyCount} accent />
        <KPICard
          label="Portfolio P&L"
          value={portLoading ? '—' : fmtINR(totalPnl, true)}
          sub={portfolio?.open_positions != null ? `${portfolio.open_positions} open positions` : undefined}
        />
        <KPICard label="Win Rate" value={portLoading ? '—' : (winRate != null ? `${winRate}%` : '—')}>
          {winRate != null && (
            <ScoreBar score={winRate} color="var(--amber)" showNumber={false} />
          )}
        </KPICard>
      </div>

      {/* Content row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 16 }}>

        {/* Signals table */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{
            padding: '14px 20px',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>Live Signals</span>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>auto-refresh 30s</span>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  {['Ticker', 'Price', 'Score', 'Signal', 'Agents', 'Updated'].map(h => (
                    <th key={h}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sigError && (
                  <tr><td colSpan={6} style={{ padding: 32, textAlign: 'center', color: 'var(--text-secondary)' }}>
                    Error loading signals — is the backend running?
                  </td></tr>
                )}
                {!sigLoading && !sigError && (!signals || signals.length === 0) && (
                  <tr><td colSpan={6} style={{ padding: 32, textAlign: 'center', color: 'var(--text-secondary)' }}>
                    No data yet — run the pipeline first.
                  </td></tr>
                )}
                {(signals || []).map(row => (
                  <tr key={row.ticker}
                      onClick={() => navigate(`/ticker/${row.ticker}`)}
                      style={{ cursor: 'pointer' }}>
                    <td style={{ fontWeight: 600, fontSize: 13 }}>{row.ticker}</td>
                    <td style={{ fontVariantNumeric: 'tabular-nums' }}>{fmtPrice(row.current_price)}</td>
                    <td style={{ width: 140 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: 12, fontWeight: 600, width: 20, color: row.composite_score >= 60 ? 'var(--green)' : row.composite_score <= 40 ? 'var(--red)' : 'var(--amber)' }}>
                          {row.composite_score ?? '—'}
                        </span>
                        <ScoreBar score={row.composite_score ?? 0} showNumber={false} />
                      </div>
                    </td>
                    <td><SignalBadge signal={row.signal} size="sm" /></td>
                    <td>
                      <div style={{ display: 'flex', gap: 4 }}>
                        {['technical_score','sentiment_score','fundamental_score'].map((k, j) => {
                          const v = row[k];
                          const bg = v >= 60 ? 'var(--green)' : v <= 40 ? 'var(--red)' : 'var(--amber)';
                          return <div key={j} title={k} style={{ width: 7, height: 7, borderRadius: '50%', background: bg, opacity: v != null ? 1 : 0.2 }} />;
                        })}
                      </div>
                    </td>
                    <td style={{ color: 'var(--text-muted)', fontVariantNumeric: 'tabular-nums' }}>
                      {row.decided_at ? new Date(row.decided_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Portfolio snapshot */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
            <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-muted)', alignSelf: 'flex-start' }}>
              Capital Deployed
            </span>
            {portLoading ? (
              <div style={{ width: 140, height: 140, borderRadius: '50%', background: 'var(--track)' }} />
            ) : (
              <DonutChart pct={deployed ?? 0} label="Deployed" />
            )}
            <div style={{ width: '100%', display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-secondary)' }}>
              <span>Available: {deployed != null ? `${100 - deployed}%` : '—'}</span>
              <span style={{ color: 'var(--green)' }}>Deployed: {deployed != null ? `${deployed}%` : '—'}</span>
            </div>
          </div>

          <div className="card">
            <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
              Quick Stats
            </span>
            <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 10 }}>
              {[
                { label: 'Total Capital', value: fmtINR(portfolio?.total_capital ?? 1000000) },
                { label: 'Deployed',      value: fmtINR(portfolio?.deployed_capital ?? 0) },
                { label: 'Total P&L',     value: fmtINR(totalPnl, true), color: pnlColor(totalPnl) },
              ].map(({ label, value, color }) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{label}</span>
                  <span style={{ fontSize: 13, fontWeight: 600, color: color || 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>{value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
