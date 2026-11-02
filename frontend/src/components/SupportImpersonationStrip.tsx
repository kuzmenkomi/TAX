import { ShieldAlert } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { supportStaff } from '../api/v1';

/** Fixed height so shell/sidebar can offset `50px` header + this bar. */
export const SUPPORT_IMPERSONATION_STRIP_H_PX = 40;

export function SupportImpersonationStrip() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const imp = user?.impersonation;
  if (!imp) return null;

  const subjectEmail = typeof imp.subject_email === 'string' ? imp.subject_email : '';
  const actorEmail = typeof imp.actor_email === 'string' ? imp.actor_email : '';

  return (
    <div
      className="flex h-10 w-full shrink-0 items-center justify-between gap-3 border-b px-3 sm:px-4"
      style={{
        background: 'rgba(245, 158, 11, 0.12)',
        borderColor: 'rgba(245, 158, 11, 0.35)',
      }}
    >
      <div className="flex min-w-0 items-center gap-2 text-[11px] font-bold sm:text-xs" style={{ color: 'var(--text)' }}>
        <ShieldAlert className="h-4 w-4 shrink-0 text-amber-500" />
        <span className="truncate">
          Support view: <span className="text-amber-600 dark:text-amber-400">{subjectEmail || 'customer'}</span>
          {actorEmail ? (
            <span className="font-normal opacity-80"> — as {actorEmail}</span>
            ) : null}
        </span>
      </div>
      <button
        type="button"
        onClick={async () => {
          try {
            await supportStaff.impersonationEnd();
          } catch {
            /* cookie may already be cleared */
          }
          await logout().catch(() => undefined);
          navigate('/login', { replace: true, state: { message: 'support_view_ended' } });
        }}
        className="shrink-0 rounded-lg bg-amber-500/90 px-3 py-1.5 text-[10px] font-extrabold uppercase tracking-wide text-black transition hover:bg-amber-400"
      >
        Exit view
      </button>
    </div>
  );
}
