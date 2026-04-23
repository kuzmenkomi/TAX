import React from 'react';

/**
 * Skeleton loading components with theme-aware pulse animation.
 */

function SkeletonPulse({ className = '', style = {} }: { className?: string; style?: React.CSSProperties }) {
  return (
    <div 
      className={`animate-pulse rounded-xl ${className}`} 
      style={{
        backgroundImage: `linear-gradient(90deg, var(--skeleton-from), var(--skeleton-via), var(--skeleton-from))`,
        backgroundSize: '200% 100%',
        ...style,
      }}
    />
  );
}

export function SkeletonCard() {
  return (
    <div className="p-6 rounded-[14px] border space-y-4" style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}>
      <div className="flex items-center justify-between">
        <SkeletonPulse className="w-10 h-10 rounded-xl" />
        <SkeletonPulse className="w-16 h-3" />
      </div>
      <SkeletonPulse className="w-12 h-2.5 opacity-40" />
      <SkeletonPulse className="w-24 h-7" />
      <SkeletonPulse className="w-16 h-2 opacity-20" />
    </div>
  );
}

export function SkeletonTable({ rows = 5 }: { rows?: number }) {
  return (
    <div className="rounded-[14px] border overflow-hidden" style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}>
      <div className="p-5 border-b flex justify-between" style={{ borderColor: 'var(--border)' }}>
        <SkeletonPulse className="w-32 h-5" />
        <SkeletonPulse className="w-20 h-5" />
      </div>
      <div className="flex gap-4 px-5 py-3 border-b" style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
        {Array.from({ length: 5 }).map((_, i) => (
          <SkeletonPulse key={i} className="h-2.5 flex-1 opacity-30" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 px-5 py-4 border-b" style={{ borderColor: 'var(--border)' }}>
          {Array.from({ length: 5 }).map((_, j) => (
            <SkeletonPulse key={j} className="h-3 flex-1 opacity-60" />
          ))}
        </div>
      ))}
    </div>
  );
}

export function SkeletonChart() {
  return (
    <div className="p-6 rounded-[14px] border" style={{ background: 'var(--card-bg)', borderColor: 'var(--border)' }}>
      <div className="flex justify-between mb-8">
        <div className="space-y-2.5">
          <SkeletonPulse className="w-32 h-5" />
          <SkeletonPulse className="w-20 h-3 opacity-40" />
        </div>
        <SkeletonPulse className="w-14 h-6 rounded-lg opacity-60" />
      </div>
      <div className="relative h-[180px]">
        <div className="absolute inset-0 flex items-end gap-3 px-2">
          {[40, 65, 50, 80, 60, 90, 75, 45, 70, 55, 85, 65].map((h, i) => (
            <div key={i} className="flex-1">
              <SkeletonPulse className="rounded-t-lg" style={{ height: `${h}%`, opacity: 0.1 + (i % 3) * 0.1 }} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function SkeletonText({ lines = 3, className = '' }: { lines?: number; className?: string }) {
  return (
    <div className={`space-y-3 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <SkeletonPulse key={i} className={`h-3 ${i === lines - 1 ? 'w-2/3' : 'w-full'}`} />
      ))}
    </div>
  );
}

export function SkeletonStatCards() {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
