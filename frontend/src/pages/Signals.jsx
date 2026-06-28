import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchSignals } from '../api/endpoints';
import SignalBadge from '../components/SignalBadge';
import ScoreBar from '../components/ScoreBar';

const fmtPrice = (n) =>
  n == null ? '—' : '₹' + new Intl.NumberFormat('en-IN', { maximumFractionDigits: 2 }).format(n);

const scoreGaugeRotation = (score) => {
  // 0=score → -45deg, 100=score → 135deg  (180 degree arc)
  return -45 + (score / 100) * 180;
};

const gaugeColor = (signal) => {
  if (signal === 'BUY') return '#00C853';
  if (signal === 'SELL') return '#FF3D00';
  return '#ffbd45';
};

const scoreNumClass = (score) => {
  if (score >= 60) return 'score-high';
  if (score <= 40) return 'score-low';
  return 'score-mid';
};

function SignalCard({ row }) {
  const color = gaugeColor(row.signal);
  const rotation = scoreGaugeRotation(row.composite_score ?? 50);
  const score = row.composite_score ?? 50;
  const techScore = row.technical_score ?? 50;
  const sentScore = row.sentiment_score ?? 50;
  const fundScore = row.fundamental_score ?? 50;
  const conf = row.confidence ?? 0;

  const updatedStr = row.decided_at
    ? new Date(row.decided_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
    : '—';

  return (
    <div className="glass-card ticker-card card-fade" style={{ borderRadius: 8, padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <h3 style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-0.01em' }}>{row.ticker}</h3>
        </div>
        <SignalBadge signal={row.signal} />
      </div>

      {/* Gauge + Score */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '8px 0' }}>
        <div className="gauge-container">
          <div className="gauge-bg" />
          <div className="gauge-fill" style={{
            borderBottomColor: color, borderLeftColor: color,
            transform: `rotate(${rotation}deg)`,
          }} />
        </div>
        <div className={`${scoreNumClass(score)}`} style={{
          fontSize: 36, fontWeight: 700, letterSpacing: '-0.02em',
          marginTop: -20, position: 'relative', zIndex: 10,
          background: '#161B22', padding: '0 8px', color: '#dae3ee',
        }}>
          {score}
        </div>
        <div style={{ fontSize: 12, fontWeight: 600, letterSpacing: '0.05em', color: '#bbcbb8', textTransform: 'uppercase', marginTop: 4 }}>
          Composite Score
        </div>
      </div>

      {/* Agent scores */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, borderTop: '1px solid #3c4a3c', paddingTop: 12 }}>
        <ScoreBar label="Technical"   score={techScore} />
        <ScoreBar label="Sentiment"   score={sentScore} />
        <ScoreBar label="Fundamental" score={fundScore} />
      </div>

      {/* Footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', borderTop: '1px solid #3c4a3c', paddingTop: 12, marginTop: 'auto' }}>
        <div>
          <div style={{ fontSize: 12, fontWeight: 600, letterSpacing: '0.05em', color: '#bbcbb8' }}>Current Price</div>
          <div style={{ fontSize: 22, fontWeight: 600 }}>{fmtPrice(row.current_price)}</div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 14, color: color, display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 4 }}>
            <span className="material-symbols-outlined" style={{ fontSize: 14 }}>bolt</span>
            Confidence {conf}%
          </div>
          <div style={{ fontSize: 10, color: '#bbcbb8', marginTop: 4 }}>Updated {updatedStr}</div>
        </div>
      </div>

      {/* View details link */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4,
        paddingTop: 8, background: 'rgba(255,255,255,0.05)', borderRadius: 4,
        padding: '8px', color: '#3fe56c', fontSize: 12, fontWeight: 600, cursor: 'pointer',
      }}>
        View Details
        <span className="material-symbols-outlined" style={{ fontSize: 16 }}>arrow_forward</span>
      </div>
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="glass-card" style={{ borderRadius: 8, padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <div className="skeleton" style={{ width: 100, height: 22 }} />
        <div className="skeleton" style={{ width: 60, height: 24, borderRadius: 9999 }} />
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
        <div className="skeleton" style={{ width: 120, height: 60, borderRadius: '50% 50% 0 0' }} />
        <div className="skeleton" style={{ width: 60, height: 36 }} />
      </div>
      {[...Array(3)].map((_, i) => (
        <div key={i} className="skeleton" style={{ height: 12 }} />
      ))}
    </div>
  );
}

export default function Signals() {
  const [filter, setFilter] = useState('ALL');

  const { data: signals, isLoading, error } = useQuery({
    queryKey: ['signals'],
    queryFn: fetchSignals,
    refetchInterval: 30000,
  });

  const filtered = (signals || []).filter(s => {
    if (filter === 'ALL') return true;
    return s.signal === filter;
  });

  const filters = ['ALL', 'BUY', 'SELL', 'HOLD'];
  const lastRun = signals?.[0]?.decided_at
    ? new Date(signals[0].decided_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
    : null;

  return (
    <main style={{ flexGrow: 1, padding: '24px 32px', maxWidth: 1440, margin: '0 auto', width: '100%' }}>
      {/* Filter bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, marginTop: 16, flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {filters.map(f => (
            <button key={f}
              className={filter === f ? 'pill-active' : 'pill-inactive'}
              style={{ padding: '6px 16px', borderRadius: 9999, fontSize: 12, fontWeight: 600, letterSpacing: '0.05em', cursor: 'pointer' }}
              onClick={() => setFilter(f === 'ALL' ? 'ALL' : f)}>
              {f === 'ALL' ? 'All Signals' : `${f} Only`}
            </button>
          ))}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 14, color: '#bbcbb8' }}>
          <span className="material-symbols-outlined" style={{ fontSize: 16 }}>sync</span>
          {lastRun ? `Last pipeline run: ${lastRun}` : 'Awaiting pipeline run'}
        </div>
      </div>

      {/* Signals grid */}
      {error && (
        <div style={{ textAlign: 'center', padding: 64, color: '#bbcbb8' }}>
          Error loading signals. Is the backend running at localhost:7999?
        </div>
      )}

      {!error && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: 16 }}>
          {isLoading && [...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
          {!isLoading && filtered.length === 0 && (
            <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: 64, color: '#bbcbb8' }}>
              {signals?.length === 0
                ? 'No data yet — run the pipeline first.'
                : `No ${filter} signals right now.`}
            </div>
          )}
          {filtered.map(row => <SignalCard key={row.ticker} row={row} />)}
        </div>
      )}
    </main>
  );
}
