import { useQuery } from '@tanstack/react-query';
import { fetchPortfolio, fetchOpenTrades, fetchTrades } from '../api/endpoints';
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

const pnlClass = (n) => n > 0 ? 'glow-green' : n < 0 ? 'glow-red' : '';
const pnlColor = (n) => n > 0 ? '#00C853' : n < 0 ? '#ffb4ab' : '#dae3ee';

function reasonPillClass(reason) {
  if (!reason) return 'pill-manual';
  const r = reason.toUpperCase();
  if (r.includes('TARGET')) return 'pill-target';
  if (r.includes('STOP')) return 'pill-stoploss';
  return 'pill-manual';
}

function SkeletonRow({ cols }) {
  return (
    <tr>
      {[...Array(cols)].map((_, i) => (
        <td key={i} style={{ padding: '16px' }}>
          <div className="skeleton" style={{ height: 12, width: i === 0 ? 80 : 60 }} />
        </td>
      ))}
    </tr>
  );
}

export default function Portfolio() {
  const { data: portfolio, isLoading: portLoading } = useQuery({
    queryKey: ['portfolio'],
    queryFn: fetchPortfolio,
    refetchInterval: 30000,
  });

  const { data: openTrades, isLoading: openLoading } = useQuery({
    queryKey: ['openTrades'],
    queryFn: fetchOpenTrades,
    refetchInterval: 30000,
  });

  const { data: allTrades, isLoading: histLoading } = useQuery({
    queryKey: ['trades'],
    queryFn: fetchTrades,
    refetchInterval: 30000,
  });

  const closedTrades = (allTrades || []).filter(t => t.status !== 'OPEN').slice(0, 20);
  const winRate = portfolio?.win_rate != null ? Math.round(portfolio.win_rate) : 0;
  const totalPnl = portfolio?.total_pnl ?? null;
  const bestTrade = portfolio?.best_trade ?? null;
  const worstTrade = portfolio?.worst_trade ?? null;

  const thStyle = { padding: '12px 16px', fontSize: 12, fontWeight: 600, letterSpacing: '0.05em', color: '#bbcbb8' };

  return (
    <main style={{ flexGrow: 1, width: '100%', maxWidth: 1600, margin: '0 auto', padding: '32px 24px', display: 'flex', flexDirection: 'column', gap: 32 }}
          className="fade-in">

      {/* Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <h1 style={{ fontSize: 32, fontWeight: 600, letterSpacing: '-0.01em' }}>Portfolio Overview</h1>
          <p style={{ fontSize: 14, color: '#bbcbb8', marginTop: 4 }}>Real-time performance and active positions</p>
        </div>
        <button style={{
          background: 'rgba(0,200,83,0.1)', color: '#3fe56c',
          border: '1px solid rgba(0,200,83,0.3)',
          padding: '8px 16px', borderRadius: 8, fontSize: 12, fontWeight: 600,
          display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer',
          transition: 'background 0.15s',
        }}>
          <span className="material-symbols-outlined" style={{ fontSize: 18 }}>download</span>
          Export Report
        </button>
      </header>

      {/* 4 KPI cards */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16 }}>
        {[
          {
            label: 'Total Capital',
            value: fmtINR(portfolio?.total_capital ?? 1000000),
            icon: 'account_balance',
          },
          {
            label: 'Deployed',
            value: fmtINR(portfolio?.deployed_capital ?? 0),
            sub: portfolio?.deployed_pct != null ? `(${Math.round(portfolio.deployed_pct * 100)}%)` : '',
            icon: 'play_arrow',
          },
          {
            label: 'Total P&L',
            value: fmtINR(totalPnl, true),
            icon: 'trending_up',
            valueColor: pnlColor(totalPnl),
            valueGlow: pnlClass(totalPnl),
            highlight: true,
          },
          {
            label: 'Win Rate',
            value: `${winRate}%`,
            icon: 'pie_chart',
            bar: true,
          },
        ].map((card, i) => (
          <div key={i} style={{
            background: '#182028', borderRadius: 8, padding: 20,
            border: `1px solid ${card.highlight ? 'rgba(0,200,83,0.15)' : '#3c4a3c'}`,
            display: 'flex', flexDirection: 'column', justifyContent: 'space-between',
            height: 128, position: 'relative', overflow: 'hidden',
            transition: 'border-color 0.2s',
          }}
            onMouseEnter={e => e.currentTarget.style.borderColor = 'rgba(63,229,108,0.2)'}
            onMouseLeave={e => e.currentTarget.style.borderColor = card.highlight ? 'rgba(0,200,83,0.15)' : '#3c4a3c'}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: 12, fontWeight: 600, letterSpacing: '0.05em', color: '#bbcbb8', textTransform: 'uppercase' }}>
                {card.label}
              </span>
              <span className="material-symbols-outlined" style={{ fontSize: 20, color: 'rgba(187,203,184,0.5)' }}>{card.icon}</span>
            </div>
            <div>
              {portLoading ? (
                <div className="skeleton" style={{ height: 36, width: 120 }} />
              ) : (
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: 12 }}>
                  <span className={card.valueGlow || ''} style={{ fontSize: 32, fontWeight: 700, letterSpacing: '-0.02em', color: card.valueColor || '#dae3ee' }}>
                    {card.value}
                  </span>
                  {card.sub && (
                    <span style={{ fontSize: 12, fontWeight: 600, color: '#bbcbb8', marginBottom: 4, background: '#222b33', padding: '2px 8px', borderRadius: 4 }}>
                      {card.sub}
                    </span>
                  )}
                  {card.bar && (
                    <div style={{ flex: 1, maxWidth: 80, height: 6, background: '#2d363e', borderRadius: 9999, overflow: 'hidden' }}>
                      <div style={{ height: '100%', background: '#3fe56c', borderRadius: 9999, width: `${winRate}%`, transition: 'width 1s ease' }} />
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </section>

      {/* Open Positions + Performance */}
      <section style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 32 }}>
        {/* Open Positions Table */}
        <div style={{ background: '#182028', borderRadius: 12, border: '1px solid #3c4a3c', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '16px 20px', borderBottom: '1px solid #3c4a3c', background: '#141c24', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 style={{ fontSize: 18, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="material-symbols-outlined" style={{ color: '#bbcbb8' }}>list_alt</span>
              Open Positions
            </h2>
            <span style={{ background: '#2d363e', color: '#bbcbb8', fontSize: 12, fontWeight: 600, padding: '4px 8px', borderRadius: 9999 }}>
              {openTrades?.length ?? 0} Active
            </span>
          </div>
          <div style={{ overflowX: 'auto', flexGrow: 1 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: 700 }}>
              <thead>
                <tr style={{ background: 'rgba(45,54,62,0.5)', borderBottom: '1px solid #3c4a3c' }}>
                  {['Ticker','Qty','Entry','Current','Unrealized P&L','Stop Loss','Days Held','Action'].map((h, i) => (
                    <th key={h} style={{ ...thStyle, textAlign: i > 1 && i !== 6 && i !== 7 ? 'right' : i === 7 ? 'center' : 'left' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody style={{ fontSize: 14 }}>
                {openLoading && [...Array(3)].map((_, i) => <SkeletonRow key={i} cols={8} />)}
                {!openLoading && (!openTrades || openTrades.length === 0) && (
                  <tr><td colSpan={8} style={{ padding: 32, textAlign: 'center', color: '#bbcbb8' }}>
                    No open positions — run the pipeline first.
                  </td></tr>
                )}
                {(openTrades || []).map((t, i) => (
                  <tr key={t.id} className="table-row" style={{ borderBottom: '1px solid #3c4a3c' }}>
                    <td style={{ padding: '16px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <div style={{ width: 8, height: 8, borderRadius: '50%', background: (t.pnl ?? 0) >= 0 ? 'rgba(0,200,83,0.2)' : 'rgba(255,100,0,0.2)', border: `1px solid ${(t.pnl ?? 0) >= 0 ? 'rgba(0,200,83,0.5)' : 'rgba(255,61,0,0.5)'}` }} />
                        <span style={{ fontWeight: 600, color: '#dae3ee' }}>{t.ticker}</span>
                      </div>
                    </td>
                    <td style={{ padding: '16px', textAlign: 'right' }}>{t.quantity}</td>
                    <td style={{ padding: '16px', textAlign: 'right', color: '#bbcbb8' }}>{fmtPrice(t.entry_price)}</td>
                    <td style={{ padding: '16px', textAlign: 'right' }}>{fmtPrice(t.current_price)}</td>
                    <td style={{ padding: '16px', textAlign: 'right' }}>
                      <span className={pnlClass(t.unrealized_pnl)} style={{ color: pnlColor(t.unrealized_pnl), fontWeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 4 }}>
                        <span className="material-symbols-outlined" style={{ fontSize: 14 }}>{(t.unrealized_pnl ?? 0) >= 0 ? 'arrow_upward' : 'arrow_downward'}</span>
                        {fmtINR(t.unrealized_pnl, true)}
                      </span>
                    </td>
                    <td style={{ padding: '16px', textAlign: 'right', color: 'rgba(255,180,171,0.8)' }}>{fmtPrice(t.stop_loss_price)}</td>
                    <td style={{ padding: '16px', textAlign: 'center', color: '#bbcbb8' }}>{t.days_held ?? '—'}</td>
                    <td style={{ padding: '16px', textAlign: 'center' }}>
                      <button style={{
                        background: '#222b33', border: '1px solid #3c4a3c',
                        color: '#bbcbb8', padding: '4px 12px', borderRadius: 4,
                        fontSize: 12, fontWeight: 600, cursor: 'pointer',
                        transition: 'background 0.15s, color 0.15s',
                      }}
                        onMouseEnter={e => { e.currentTarget.style.background = '#313a43'; e.currentTarget.style.color = '#dae3ee'; }}
                        onMouseLeave={e => { e.currentTarget.style.background = '#222b33'; e.currentTarget.style.color = '#bbcbb8'; }}>
                        Close
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Performance panel */}
        <div style={{ background: '#182028', borderRadius: 12, border: '1px solid #3c4a3c', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '16px 20px', borderBottom: '1px solid #3c4a3c', background: '#141c24' }}>
            <h2 style={{ fontSize: 18, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="material-symbols-outlined" style={{ color: '#bbcbb8' }}>donut_large</span>
              Performance
            </h2>
          </div>
          <div style={{ padding: 20, flexGrow: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 24 }}>
            {portLoading ? (
              <div className="skeleton" style={{ width: 192, height: 192, borderRadius: '50%' }} />
            ) : (
              <DonutChart pct={winRate} />
            )}
            <div style={{ width: '100%', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div style={{ background: '#222b33', borderRadius: 8, padding: 12, border: '1px solid rgba(60,74,60,0.5)' }}>
                <span style={{ display: 'block', fontSize: 10, fontWeight: 600, letterSpacing: '0.05em', color: '#bbcbb8', textTransform: 'uppercase', marginBottom: 4 }}>Best Trade</span>
                <span className="glow-green" style={{ display: 'block', fontSize: 16, fontWeight: 500, color: '#00C853' }}>
                  {bestTrade != null ? fmtINR(bestTrade, true) : '—'}
                </span>
              </div>
              <div style={{ background: '#222b33', borderRadius: 8, padding: 12, border: '1px solid rgba(60,74,60,0.5)' }}>
                <span style={{ display: 'block', fontSize: 10, fontWeight: 600, letterSpacing: '0.05em', color: '#bbcbb8', textTransform: 'uppercase', marginBottom: 4 }}>Worst Trade</span>
                <span className="glow-red" style={{ display: 'block', fontSize: 16, fontWeight: 500, color: '#ffb4ab' }}>
                  {worstTrade != null ? fmtINR(worstTrade) : '—'}
                </span>
              </div>
              <div style={{ background: '#222b33', borderRadius: 8, padding: 12, border: '1px solid rgba(60,74,60,0.5)', gridColumn: '1/-1', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <span style={{ display: 'block', fontSize: 10, fontWeight: 600, letterSpacing: '0.05em', color: '#bbcbb8', textTransform: 'uppercase', marginBottom: 4 }}>Avg P&L / Trade</span>
                  <span style={{ display: 'block', fontSize: 16, fontWeight: 500, color: '#dae3ee' }}>
                    {portfolio?.avg_pnl_per_trade != null ? fmtINR(portfolio.avg_pnl_per_trade, true) : '—'}
                  </span>
                </div>
                <div style={{ width: 48, height: 24, background: '#2d363e', borderRadius: 9999, overflow: 'hidden', display: 'flex', alignItems: 'flex-end' }}>
                  {[30,70,40,90].map((h, i) => (
                    <div key={i} style={{ flex: 1, height: `${h}%`, background: i === 2 ? 'rgba(255,180,171,0.7)' : `rgba(63,229,108,${0.4 + i*0.2})`, margin: '0 1px', borderRadius: '2px 2px 0 0' }} />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Trade History */}
      <section style={{ background: '#182028', borderRadius: 12, border: '1px solid #3c4a3c', overflow: 'hidden', marginTop: 16 }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #3c4a3c', background: '#141c24', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className="material-symbols-outlined" style={{ color: '#bbcbb8' }}>history</span>
            Trade History
          </h2>
          <button style={{
            background: '#222b33', border: '1px solid #3c4a3c',
            color: '#bbcbb8', padding: '6px 12px', borderRadius: 4,
            fontSize: 12, fontWeight: 600, cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: 4,
            transition: 'background 0.15s',
          }}>
            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>filter_list</span>
            Filter
          </button>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: 900 }}>
            <thead>
              <tr style={{ background: 'rgba(45,54,62,0.5)', borderBottom: '1px solid #3c4a3c' }}>
                {['Date','Ticker','Action','Entry','Exit','P&L','P&L %','Reason'].map((h, i) => (
                  <th key={h} style={{ ...thStyle, textAlign: i > 2 && i < 7 ? 'right' : i === 7 ? 'center' : 'left' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody style={{ fontSize: 14 }}>
              {histLoading && [...Array(3)].map((_, i) => <SkeletonRow key={i} cols={8} />)}
              {!histLoading && closedTrades.length === 0 && (
                <tr><td colSpan={8} style={{ padding: 32, textAlign: 'center', color: '#bbcbb8' }}>
                  No trade history yet.
                </td></tr>
              )}
              {closedTrades.map((t, i) => (
                <tr key={t.id} className="table-row" style={{ borderBottom: '1px solid #3c4a3c' }}>
                  <td style={{ padding: '16px', color: '#bbcbb8' }}>
                    {t.exited_at ? new Date(t.exited_at).toLocaleString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}
                  </td>
                  <td style={{ padding: '16px', fontWeight: 600, color: '#dae3ee' }}>{t.ticker}</td>
                  <td style={{ padding: '16px' }}>
                    <span style={{ color: t.action === 'BUY' ? '#00C853' : '#ffb4ab', fontWeight: 500 }}>{t.action}</span>
                  </td>
                  <td style={{ padding: '16px', textAlign: 'right', color: '#bbcbb8' }}>{fmtPrice(t.entry_price)}</td>
                  <td style={{ padding: '16px', textAlign: 'right' }}>{fmtPrice(t.exit_price)}</td>
                  <td style={{ padding: '16px', textAlign: 'right' }}>
                    <span className={pnlClass(t.pnl)} style={{ color: pnlColor(t.pnl), fontWeight: 600 }}>
                      {fmtINR(t.pnl, true)}
                    </span>
                  </td>
                  <td style={{ padding: '16px', textAlign: 'right' }}>
                    <span style={{ color: pnlColor(t.pnl_pct) }}>
                      {t.pnl_pct != null ? `${t.pnl_pct >= 0 ? '+' : ''}${t.pnl_pct.toFixed(2)}%` : '—'}
                    </span>
                  </td>
                  <td style={{ padding: '16px', textAlign: 'center' }}>
                    <span className={`${reasonPillClass(t.exit_reason)}`}
                          style={{ display: 'inline-block', borderRadius: 9999, padding: '2px 8px', fontSize: 10, fontWeight: 600, letterSpacing: '0.05em' }}>
                      {t.exit_reason || 'MANUAL'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {closedTrades.length > 0 && (
          <div style={{ padding: 16, borderTop: '1px solid #3c4a3c', display: 'flex', justifyContent: 'center' }}>
            <button style={{ color: '#bbcbb8', fontSize: 12, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4, transition: 'color 0.15s' }}
                    onMouseEnter={e => e.currentTarget.style.color = '#dae3ee'}
                    onMouseLeave={e => e.currentTarget.style.color = '#bbcbb8'}>
              Load More
              <span className="material-symbols-outlined" style={{ fontSize: 18 }}>expand_more</span>
            </button>
          </div>
        )}
      </section>
    </main>
  );
}
