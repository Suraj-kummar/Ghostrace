import React from 'react';

type BadgeVariant = 'success' | 'warning' | 'error' | 'info' | 'neutral' | 'purple';

interface BadgeProps {
  label: string;
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
}

const variantStyles: Record<BadgeVariant, string> = {
  success: 'background: rgba(16,185,129,0.15); color: #10b981; border-color: rgba(16,185,129,0.3);',
  warning: 'background: rgba(245,158,11,0.15); color: #f59e0b; border-color: rgba(245,158,11,0.3);',
  error: 'background: rgba(239,68,68,0.15); color: #ef4444; border-color: rgba(239,68,68,0.3);',
  info: 'background: rgba(59,130,246,0.15); color: #3b82f6; border-color: rgba(59,130,246,0.3);',
  neutral: 'background: rgba(148,163,184,0.15); color: #94a3b8; border-color: rgba(148,163,184,0.3);',
  purple: 'background: rgba(168,85,247,0.15); color: #a855f7; border-color: rgba(168,85,247,0.3);',
};

const Badge: React.FC<BadgeProps> = ({ label, variant = 'neutral', size = 'sm' }) => {
  const sizeStyle = size === 'sm'
    ? 'font-size: 0.7rem; padding: 2px 8px;'
    : 'font-size: 0.75rem; padding: 4px 10px;';

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        borderRadius: '999px',
        border: '1px solid',
        fontWeight: 600,
        letterSpacing: '0.03em',
        whiteSpace: 'nowrap',
        ...(Object.fromEntries(
          variantStyles[variant]
            .split(';')
            .filter(Boolean)
            .map(s => {
              const [k, v] = s.split(':').map(x => x.trim());
              const camel = k.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
              return [camel, v];
            })
        )),
        ...(Object.fromEntries(
          sizeStyle
            .split(';')
            .filter(Boolean)
            .map(s => {
              const [k, v] = s.split(':').map(x => x.trim());
              const camel = k.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
              return [camel, v];
            })
        )),
      }}
    >
      {label}
    </span>
  );
};

export default Badge;
