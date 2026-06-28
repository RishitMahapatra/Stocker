import { useEffect, useRef } from 'react';

function colorFor(score) {
  if (score >= 60) return 'var(--green)';
  if (score <= 40) return 'var(--red)';
  return 'var(--amber)';
}

export default function ScoreBar({ score = 0, color, label, showNumber = true }) {
  const fillRef = useRef(null);

  useEffect(() => {
    const el = fillRef.current;
    if (!el) return;
    const id = requestAnimationFrame(() => { el.style.width = `${Math.min(100, Math.max(0, score))}%`; });
    return () => cancelAnimationFrame(id);
  }, [score]);

  const c = color || colorFor(score);

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      {label && (
        <span style={{ fontSize: 12, color: 'var(--text-secondary)', flex: '0 0 80px' }}>{label}</span>
      )}
      <div className="score-track">
        <div ref={fillRef} className="score-fill" style={{ background: c }} />
      </div>
      {showNumber && (
        <span style={{ fontSize: 11, fontWeight: 600, color: c, width: 22, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
          {score}
        </span>
      )}
    </div>
  );
}
