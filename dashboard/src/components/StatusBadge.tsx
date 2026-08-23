'use client';

interface StatusBadgeProps {
  status: 'detected' | 'missed' | 'blocked' | 'approved' | 'pending' | 'filed' | 'running' | 'stopped';
  size?: 'sm' | 'md' | 'lg';
}

export function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  const configs = {
    detected: { label: 'DETECTED', className: 'status-chip success', dot: 'bg-[var(--success-green)]' },
    blocked: { label: 'BLOCKED', className: 'status-chip success', dot: 'bg-[var(--success-green)]' },
    missed: { label: 'MISSED', className: 'status-chip danger', dot: 'bg-[var(--danger-red)]' },
    approved: { label: 'APPROVED', className: 'status-chip success', dot: 'bg-[var(--success-green)]' },
    pending: { label: 'PENDING', className: 'status-chip warning', dot: 'bg-[var(--warning-clay)]' },
    filed: { label: 'FILED', className: 'status-chip success', dot: 'bg-[var(--success-green)]' },
    running: { label: 'LIVE', className: 'status-chip info', dot: 'bg-[var(--link-blue)]' },
    stopped: { label: 'STOPPED', className: 'status-chip', dot: 'bg-[var(--dust-taupe)]' },
  };

  const config = configs[status];
  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-xs',
    lg: 'px-4 py-1.5 text-sm',
  };

  return (
    <span className={`${config.className} ${sizes[size]} flex items-center gap-1.5`}>
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} aria-hidden="true"></span>
      {config.label}
    </span>
  );
}