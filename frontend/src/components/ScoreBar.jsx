import { useEffect, useRef } from 'react';

const colorFor = (score, color) => {
  if (color) return color;
  if (score >= 60) return '#00C853';
  if (score <= 40) return '#FF3D00';
  return '#ffbd45';
};

export default function ScoreBar({ score = 0, color, label, showNumber = true }) {
  const fillRef = useRef(null);

  useEffect(() => {
    const el = fillRef.current;
    if (!el) return;
    // Defer to next frame so CSS transition fires
    const id = requestAnimationFrame(() => { el.style.width = `${score}%`; });
    return () => cancelAnimationFrame(id);
  }, [score]);

  const c = colorFor(score, color);

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      {label && (
        <span style={{ fontSize: 14, color: '#bbcbb8', flex: '0 0 80px' }}>{label}</span>
      )}
      <div className="score-track" style={{ flex: 1 }}>
        <div ref={fillRef} className="score-fill" style={{ background: c }} />
      </div>
      {showNumber && (
        <span style={{ fontSize: 12, fontWeight: 600, color: c, width: 24, textAlign: 'right' }}>
          {score}
        </span>
      )}
    </div>
  );
}
