import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchSignal, fetchSignalHistory, fetchPrices } from '../api/endpoints';
import SignalBadge from '../components/SignalBadge';
import ScoreBar from '../components/ScoreBar';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const fmtPrice = (n) =>
  n == null ? '—' : '₹' + new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 }).format(n);

const scoreColor = (s) => s >= 60 ? 'var(--green)' : s <= 40 ? 'var(--red)' : 'var(--amber)';

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'var(--bg-elevated)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 6, padding: '8px 12px',
      fontSize: 12,
    }}>
      <div style={{ color: 'var(--text-muted)', marginBottom: 4 }}>{label}</div>
      <div style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
        {fmtPrice(payload[0].value)}
      </div>
    </div>
  );
}

export default function TickerDetail() {
  const { ticker } = useParams();
  const navigate = useNavigate();

  const { data: signal, isLoading: sigLoading } = useQuery({
    queryKey: ['signal', ticker],
    queryFn: () => fetchSignal(ticker),
    refetchInterval: 30000,
  });

  const { data: history } = useQuery({
    queryKey: ['signalHistory', ticker],
    queryFn: () => fetchSignalHistory(ticker, 10),
    refetchInterval: 60000,
  });

  const { data: prices } = useQuery({
    queryKey: ['prices', ticker],
    queryFn: () => fetchPrices(ticker, 30),
    refetchInterval: 60000,
  });

  const priceData = (prices || []).map(p => ({
    date: new Date(p.date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }),
    price: p.close,
  }));

  const score = signal?.composite_score ?? 50;

  return (
    <main className="page-enter" style={{ padding: '24px', maxWidth: 1280, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* Back + header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <button
          onClick={() => navigate(-1)}
          style={{
            fontSize: 12, color: 'var(--text-secondary)', background: 'none',
            border: '1px solid var(--border-subtle)', padding: '4px 10px', borderRadius: 4, cursor: 'pointer',
          }}>
          ← Back
        </button>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 22, fontWeight: 700 }}>{ticker}</span>
          {!sigLoading && signal && <SignalBadge signal={signal.signal} />}
        </div>
        {signal && (
          <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{fmtPrice(signal.current_price)}</span>
        )}
      </div>

      {/* Top row: price chart + current decision */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 16 }}>

        {/* Price chart */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>30-Day Price History</span>
          </div>
          <div style={{ padding: '20px', height: 260 }}>
            {!priceData.length ? (
              <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 12 }}>
                No price data available
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={priceData} margin={{ top: 4, right: 8, bottom: 4, left: 8 }}>
                  <CartesianGrid stroke="var(--border-subtle)" strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 10, fill: 'var(--text-muted)' }}
                    axisLine={false} tickLine={false}
                    interval="preserveStartEnd"
                  />
                  <YAxis
                    tick={{ fontSize: 10, fill: 'var(--text-muted)' }}
                    axisLine={false} tickLine={false}
                    tickFormatter={v => '₹' + new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(v)}
                    width={72}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Line
                    type="monotone"
                    dataKey="price"
                    stroke="var(--green)"
                    strokeWidth={1.5}
                    dot={false}
                    activeDot={{ r: 3, fill: 'var(--green)' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Current decision card */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
            Current Decision
          </span>

          {sigLoading ? (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 12 }}>
              Loading…
            </div>
          ) : signal ? (
            <>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
                <span style={{ fontSize: 40, fontWeight: 700, color: scoreColor(score), fontVariantNumeric: 'tabular-nums' }}>{score}</span>
                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>/ 100</span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <ScoreBar label="Technical"   score={signal.technical_score   ?? 50} />
                <ScoreBar label="Sentiment"   score={signal.sentiment_score   ?? 50} />
                <ScoreBar label="Fundamental" score={signal.fundamental_score ?? 50} />
              </div>

              <div style={{ padding: '12px 0', borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Confidence</span>
                <span style={{ fontSize: 13, fontWeight: 600 }}>{signal.confidence ?? 0}%</span>
              </div>

              {signal.reasoning && (
                <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6, borderTop: '1px solid var(--border-subtle)', paddingTop: 12 }}>
                  {signal.reasoning}
                </p>
              )}
            </>
          ) : (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 12 }}>
              No signal data for {ticker}
            </div>
          )}
        </div>
      </div>

      {/* Signal history */}
      {history && history.length > 0 && (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Decision History</span>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: 'var(--bg-deep)' }}>
                  {['Date', 'Signal', 'Score', 'Technical', 'Sentiment', 'Fundamental', 'Confidence'].map(h => (
                    <th key={h} style={{ padding: '10px 16px', fontSize: 11, fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase', color: 'var(--text-muted)', borderBottom: '1px solid var(--border-subtle)', textAlign: 'left' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {history.map((row, i) => (
                  <tr key={i}>
                    <td style={{ padding: '12px 16px', fontSize: 12, color: 'var(--text-secondary)', borderBottom: '1px solid var(--border-subtle)', fontVariantNumeric: 'tabular-nums' }}>
                      {row.decided_at ? new Date(row.decided_at).toLocaleString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}
                    </td>
                    <td style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
                      <SignalBadge signal={row.signal} size="sm" />
                    </td>
                    {['composite_score','technical_score','sentiment_score','fundamental_score'].map(k => (
                      <td key={k} style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)', fontVariantNumeric: 'tabular-nums' }}>
                        <span style={{ color: scoreColor(row[k] ?? 50), fontWeight: 600 }}>{row[k] ?? '—'}</span>
                      </td>
                    ))}
                    <td style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-secondary)', fontVariantNumeric: 'tabular-nums' }}>
                      {row.confidence ?? '—'}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </main>
  );
}
