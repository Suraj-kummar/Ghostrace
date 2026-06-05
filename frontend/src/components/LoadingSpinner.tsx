import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  color?: string;
  label?: string;
}

const sizes = { sm: 18, md: 32, lg: 48 };

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  color = '#a78bfa',
  label = 'Loading…',
}) => {
  const px = sizes[size];

  return (
    <span
      role="status"
      aria-label={label}
      style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}
    >
      <svg
        width={px}
        height={px}
        viewBox="0 0 50 50"
        style={{ animation: 'spin 0.8s linear infinite' }}
      >
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        <circle
          cx="25"
          cy="25"
          r="20"
          fill="none"
          stroke="rgba(167,139,250,0.2)"
          strokeWidth="5"
        />
        <circle
          cx="25"
          cy="25"
          r="20"
          fill="none"
          stroke={color}
          strokeWidth="5"
          strokeLinecap="round"
          strokeDasharray="80 40"
        />
      </svg>
      {size === 'lg' && (
        <span style={{ color: 'var(--text-secondary, #94a3b8)', fontSize: '0.85rem' }}>{label}</span>
      )}
    </span>
  );
};

export default LoadingSpinner;
