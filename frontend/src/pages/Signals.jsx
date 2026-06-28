import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { fetchSignals } from '../api/endpoints';
import SignalBadge from '../components/SignalBadge';
import ScoreBar from '../components/ScoreBar';

const fmtPrice = (n) =>
  n == null ? '—' : '₹' + new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 }).format(n);

const scoreColor = (s) => s >= 60 ? 'var(--green)' : s <= 40 ? 'var(--red)' : 'var(--amber)';

function SignalCard({ row }) {
  const navigate = useNavigate();
  const score = row.composite_score ?? 50;
  const conf = row.confidence ?? 0;
  const updatedStr = row.decided_at
    ? new Date(row.decided_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
    : '—';

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>{row.ticker}</div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>{fmtPrice(row.current_price)}</div>
        </div>
        <SignalBadge signal={row.signal} />
      </div>

      {/* Score display */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 0', borderTop: '1px solid var(--border-subtle)', borderBottom: '1px solid var(--border-subtle)' }}>
        <span style={{ fontSize: 32, fontWeight: 700, letterSpacing: '-0.02em', color: scoreColor(score), fontVariantNumeric: 'tabular-nums' }}>
          {score}
        </span>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 4 }}>
          <span style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
            Composite Score
          </span>
          <ScoreBar score={score} showNumber={false} />
          <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Confidence {conf}%</span>
        </div>
      </div>

      {/* Agent breakdown */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <ScoreBar label="Technical"   score={row.technical_score   ?? 50} />
        <ScoreBar label="Sentiment"   score={row.sentiment_score   ?? 50} />
        <ScoreBar label="Fundamental" score={row.fundamental_score ?? 50} />
      </div>

      {/* Footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Updated {updatedStr}</span>
        <button
          onClick={() => navigate(`/ticker/${row.ticker}`)}
          style={{
            fontSize: 11, fontWeight: 600, color: 'var(--green)',
            background: 'var(--green-dim)', border: '1px solid var(--green-border)',
            padding: '4px 10px', borderRadius: 4, cursor: 'pointer',
          }}>
          View Details →
        </button>
      </div>
    </div>
  );
}

const FILTERS = ['ALL', 'BUY', 'SELL', 'HOLD'];

export default function Signals() {
  const [filter, setFilter] = useState('ALL');

  const { data: signals, isLoading, error } = useQuery({
    queryKey: ['signals'],
    queryFn: fetchSignals,
    refetchInterval: 30000,
  });

  const filtered = (signals || []).filter(s => filter === 'ALL' || s.signal === filter);
  const lastRun = signals?.[0]?.decided_at
    ? new Date(signals[0].decided_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
    : null;

  const pillBase = {
    fontSize: 11, fontWeight: 600, letterSpacing: '0.05em',
    padding: '4px 12px', borderRadius: 4, cursor: 'pointer', border: '1px solid var(--border-subtle)',
  };

  return (
    <main className="page-enter" style={{ padding: '24px', maxWidth: 1280, margin: '0 auto' }}>
      {/* Toolbar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', gap: 6 }}>
          {FILTERS.map(f => (
            <button key={f}
              onClick={() => setFilter(f)}
              style={{
                ...pillBase,
                background: filter === f ? 'var(--bg-elevated)' : 'transparent',
                color: filter === f ? 'var(--text-primary)' : 'var(--text-secondary)',
                borderColor: filter === f ? 'var(--border-hover)' : 'var(--border-subtle)',
              }}>
              {f === 'ALL' ? 'All' : f}
              {f !== 'ALL' && signals && (
                <span style={{ marginLeft: 5, opacity: 0.6 }}>
                  {(signals || []).filter(s => s.signal === f).length}
                </span>
              )}
            </button>
          ))}
        </div>
        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
          {lastRun ? `Last run ${lastRun}` : 'Awaiting pipeline'}
        </span>
      </div>

      {error && (
        <div style={{ textAlign: 'center', padding: 64, color: 'var(--text-secondary)' }}>
          Error loading signals — is the backend running at localhost:7999?
        </div>
      )}

      {!error && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 12 }}>
          {isLoading && [...Array(4)].map((_, i) => (
            <div key={i} className="card" style={{ height: 280, opacity: 0.4 }} />
          ))}
          {!isLoading && filtered.length === 0 && (
            <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: 64, color: 'var(--text-secondary)' }}>
              {!signals?.length ? 'No data — run the pipeline first.' : `No ${filter} signals.`}
            </div>
          )}
          {filtered.map(row => <SignalCard key={row.ticker} row={row} />)}
        </div>
      )}
    </main>
  );
}
