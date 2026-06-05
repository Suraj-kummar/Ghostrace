import React, { useState } from 'react';
import Tooltip from './Tooltip';

interface CopyButtonProps {
  text: string;
  label?: string;
  successLabel?: string;
  size?: 'sm' | 'md';
}

const CopyButton: React.FC<CopyButtonProps> = ({
  text,
  label = 'Copy',
  successLabel = 'Copied!',
  size = 'sm',
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers
      const el = document.createElement('textarea');
      el.value = text;
      document.body.appendChild(el);
      el.select();
      document.execCommand('copy');
      document.body.removeChild(el);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const sizeStyle = size === 'sm'
    ? { fontSize: '0.72rem', padding: '4px 10px', gap: '4px' }
    : { fontSize: '0.82rem', padding: '7px 14px', gap: '6px' };

  return (
    <Tooltip content={copied ? 'Copied to clipboard!' : `Copy to clipboard`}>
      <button
        onClick={handleCopy}
        aria-label={copied ? successLabel : label}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          borderRadius: '6px',
          border: `1px solid ${copied ? 'rgba(16,185,129,0.4)' : 'rgba(148,163,184,0.2)'}`,
          background: copied ? 'rgba(16,185,129,0.1)' : 'rgba(148,163,184,0.08)',
          color: copied ? '#10b981' : '#94a3b8',
          fontWeight: 600,
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          fontFamily: 'inherit',
          ...sizeStyle,
        }}
      >
        <span>{copied ? '✓' : '⎘'}</span>
        <span>{copied ? successLabel : label}</span>
      </button>
    </Tooltip>
  );
};

export default CopyButton;
