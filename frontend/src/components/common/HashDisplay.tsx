import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';

interface HashDisplayProps {
  hash: string | null | undefined;
  label?: string;
  truncateLength?: number;
}

export const HashDisplay: React.FC<HashDisplayProps> = ({
  hash,
  label,
  truncateLength = 12,
}) => {
  const [copied, setCopied] = useState(false);

  if (!hash) {
    return <span style={{ color: 'var(--text-muted)' }}>N/A</span>;
  }

  const truncated =
    hash.length > truncateLength * 2
      ? `${hash.slice(0, truncateLength)}...${hash.slice(-truncateLength)}`
      : hash;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(hash);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.4rem',
        fontFamily: 'var(--font-mono)',
        fontSize: '0.8rem',
        background: 'var(--bg-input)',
        padding: '0.2rem 0.5rem',
        borderRadius: 'var(--radius-sm)',
        border: '1px solid var(--border-subtle)',
      }}
      title={hash}
    >
      {label && <span style={{ color: 'var(--text-muted)' }}>{label}:</span>}
      <span style={{ color: 'var(--accent-cyan)' }}>{truncated}</span>
      <button
        onClick={handleCopy}
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          padding: 0,
          display: 'inline-flex',
          alignItems: 'center',
          color: copied ? 'var(--verdict-accept)' : 'var(--text-muted)',
          transition: 'color var(--transition-fast)',
        }}
        title="Copy full hash to clipboard"
        aria-label="Copy hash"
      >
        {copied ? <Check size={13} /> : <Copy size={13} />}
      </button>
    </span>
  );
};
