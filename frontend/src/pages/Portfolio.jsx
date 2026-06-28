import { useQuery } from '@tanstack/react-query';
import { fetchPortfolio, fetchOpenTrades, fetchTrades } from '../api/endpoints';
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

const TH = ({ children, align = 'left' }) => (
  <th style={{ padding: '10px 16px', fontSize: 11, fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase', color: 'var(--text-muted)', borderBottom: '1px solid var(--border-subtle)', textAlign: align }}>
    {children}
  </th>
);

const TD = ({ children, align = 'left', style: s }) => (
  <td style={{ padding: '13px 16px', borderBottom: '1px solid var(--border-subtle)', fontSize: 14, textAlign: align, ...s }}>
    {children}
  </td>
);

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
  const winRate  = portfolio?.win_rate != null ? Math.round(portfolio.win_rate) : 0;
  const totalPnl = portfolio?.total_pnl ?? null;
  const deployed = portfolio?.deployed_pct != null ? Math.round(portfolio.deployed_pct * 100) : 0;

  return (
    <main className="page-enter" style={{ padding: '24px', maxWidth: 1440, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12 }}>
        <KPICard label="Total Capital"    value={portLoading ? '—' : fmtINR(portfolio?.total_capital ?? 1000000)} />
        <KPICard label="Deployed Capital" value={portLoading ? '—' : fmtINR(portfolio?.deployed_capital ?? 0)}
                 sub={deployed ? `${deployed}% of capital` : undefined} />
        <KPICard label="Total P&L" value={portLoading ? '—' : fmtINR(totalPnl, true)} accent>
          {totalPnl != null && (
            <span style={{ fontSize: 12, color: pnlColor(totalPnl) }}>
              {totalPnl >= 0 ? '▲' : '▼'} {Math.abs(((totalPnl / (portfolio?.total_capital || 1)) * 100)).toFixed(2)}%
            </span>
          )}
        </KPICard>
        <KPICard label="Win Rate" value={portLoading ? '—' : `${winRate}%`} />
      </div>

      {/* Open Positions + Performance */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 16 }}>

        {/* Open positions table */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Open Positions</span>
            <span style={{
              fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 4,
              background: 'var(--bg-elevated)', color: 'var(--text-secondary)',
            }}>
              {openTrades?.length ?? 0} active
            </span>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 640 }}>
              <thead>
                <tr style={{ background: 'var(--bg-deep)' }}>
                  <TH>Ticker</TH>
                  <TH align="right">Qty</TH>
                  <TH align="right">Entry</TH>
                  <TH align="right">Current</TH>
                  <TH align="right">Unrealized P&L</TH>
                  <TH align="right">Stop Loss</TH>
                  <TH align="center">Days</TH>
                </tr>
              </thead>
              <tbody>
                {!openLoading && (!openTrades || openTrades.length === 0) && (
                  <tr><td colSpan={7} style={{ padding: 32, textAlign: 'center', color: 'var(--text-secondary)' }}>
                    No open positions.
                  </td></tr>
                )}
                {(openTrades || []).map(t => (
                  <tr key={t.id} style={{ cursor: 'default' }}>
                    <TD><span style={{ fontWeight: 600 }}>{t.ticker}</span></TD>
                    <TD align="right">{t.quantity}</TD>
                    <TD align="right" style={{ color: 'var(--text-secondary)', fontVariantNumeric: 'tabular-nums' }}>{fmtPrice(t.entry_price)}</TD>
                    <TD align="right" style={{ fontVariantNumeric: 'tabular-nums' }}>{fmtPrice(t.current_price)}</TD>
                    <TD align="right">
                      <span style={{ color: pnlColor(t.unrealized_pnl), fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
                        {fmtINR(t.unrealized_pnl, true)}
                      </span>
                    </TD>
                    <TD align="right" style={{ color: 'var(--red)', fontSize: 12, fontVariantNumeric: 'tabular-nums' }}>{fmtPrice(t.stop_loss_price)}</TD>
                    <TD align="center" style={{ color: 'var(--text-muted)' }}>{t.days_held ?? '—'}</TD>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Performance panel */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 20 }}>
          <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-muted)', alignSelf: 'flex-start' }}>
            Performance
          </span>
          {portLoading ? (
            <div style={{ width: 140, height: 140, borderRadius: '50%', background: 'var(--track)' }} />
          ) : (
            <DonutChart pct={winRate} />
          )}
          <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: 10 }}>
            {[
              { label: 'Best Trade',    value: fmtINR(portfolio?.best_trade, true),  color: 'var(--green)' },
              { label: 'Worst Trade',   value: fmtINR(portfolio?.worst_trade),        color: 'var(--red)'   },
              { label: 'Avg P&L/Trade', value: fmtINR(portfolio?.avg_pnl_per_trade, true) },
            ].map(({ label, value, color }) => (
              <div key={label} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{label}</span>
                <span style={{ fontSize: 13, fontWeight: 600, color: color || 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>{value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Trade history */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
          <span style={{ fontSize: 13, fontWeight: 600 }}>Trade History</span>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 800 }}>
            <thead>
              <tr style={{ background: 'var(--bg-deep)' }}>
                <TH>Date</TH>
                <TH>Ticker</TH>
                <TH>Action</TH>
                <TH align="right">Entry</TH>
                <TH align="right">Exit</TH>
                <TH align="right">P&L</TH>
                <TH align="right">P&L %</TH>
                <TH align="center">Reason</TH>
              </tr>
            </thead>
            <tbody>
              {!histLoading && closedTrades.length === 0 && (
                <tr><td colSpan={8} style={{ padding: 32, textAlign: 'center', color: 'var(--text-secondary)' }}>
                  No trade history yet.
                </td></tr>
              )}
              {closedTrades.map(t => {
                const reason = (t.exit_reason || 'MANUAL').toUpperCase();
                const reasonColor = reason.includes('TARGET') ? 'var(--green)' : reason.includes('STOP') ? 'var(--red)' : 'var(--text-muted)';
                const reasonBg   = reason.includes('TARGET') ? 'var(--green-dim)' : reason.includes('STOP') ? 'var(--red-dim)' : 'var(--bg-elevated)';
                return (
                  <tr key={t.id}>
                    <TD style={{ color: 'var(--text-secondary)', fontSize: 12, fontVariantNumeric: 'tabular-nums' }}>
                      {t.exited_at ? new Date(t.exited_at).toLocaleString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}
                    </TD>
                    <TD><span style={{ fontWeight: 600 }}>{t.ticker}</span></TD>
                    <TD>
                      <span style={{ color: t.action === 'BUY' ? 'var(--green)' : 'var(--red)', fontWeight: 600, fontSize: 12 }}>{t.action}</span>
                    </TD>
                    <TD align="right" style={{ color: 'var(--text-secondary)', fontVariantNumeric: 'tabular-nums' }}>{fmtPrice(t.entry_price)}</TD>
                    <TD align="right" style={{ fontVariantNumeric: 'tabular-nums' }}>{fmtPrice(t.exit_price)}</TD>
                    <TD align="right">
                      <span style={{ color: pnlColor(t.pnl), fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>{fmtINR(t.pnl, true)}</span>
                    </TD>
                    <TD align="right">
                      <span style={{ color: pnlColor(t.pnl_pct), fontVariantNumeric: 'tabular-nums' }}>
                        {t.pnl_pct != null ? `${t.pnl_pct >= 0 ? '+' : ''}${t.pnl_pct.toFixed(2)}%` : '—'}
                      </span>
                    </TD>
                    <TD align="center">
                      <span style={{ fontSize: 10, fontWeight: 600, padding: '2px 7px', borderRadius: 4, color: reasonColor, background: reasonBg }}>
                        {reason}
                      </span>
                    </TD>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
}
