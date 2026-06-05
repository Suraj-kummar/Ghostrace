import React from 'react';

interface EmptyStateProps {
  icon?: string;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

const EmptyState: React.FC<EmptyStateProps> = ({
  icon = '📭',
  title,
  description,
  actionLabel,
  onAction,
}) => (
  <div
    style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '16px',
      padding: '64px 32px',
      textAlign: 'center',
      color: 'var(--text-secondary, #94a3b8)',
    }}
  >
    <div style={{ fontSize: '3rem', lineHeight: 1 }}>{icon}</div>
    <div>
      <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--text-primary, #e2e8f0)', margin: '0 0 6px' }}>
        {title}
      </h3>
      {description && (
        <p style={{ fontSize: '0.85rem', margin: 0, maxWidth: '320px' }}>{description}</p>
      )}
    </div>
    {actionLabel && onAction && (
      <button
        onClick={onAction}
        style={{
          background: 'linear-gradient(135deg, #7c3aed, #a78bfa)',
          color: '#fff',
          border: 'none',
          borderRadius: '8px',
          padding: '10px 24px',
          fontSize: '0.85rem',
          fontWeight: 600,
          cursor: 'pointer',
          transition: 'opacity 0.2s',
        }}
        onMouseOver={e => (e.currentTarget.style.opacity = '0.85')}
        onMouseOut={e => (e.currentTarget.style.opacity = '1')}
      >
        {actionLabel}
      </button>
    )}
  </div>
);

export default EmptyState;
