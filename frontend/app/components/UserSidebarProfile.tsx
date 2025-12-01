// app/components/UserSidebarProfile.tsx
'use client';

import { useRouter } from 'next/navigation';

interface UserSidebarProfileProps {
  name: string;
  jobTitle?: string;
  image128?: string | null;
}

export const UserSidebarProfile: React.FC<UserSidebarProfileProps> = ({
  name,
  jobTitle,
  image128,
}) => {
  const router = useRouter();

  const onLogout = async () => {
    try {
      await fetch('/api/session/logout', {
        method: 'POST',
      });
      router.replace('/login');
    } catch (e) {
      console.error('Logout error', e);
    }
  };

  return (
    <div className="flex items-center gap-3 p-3 border-t border-slate-200">
      {image128 ? (
        <img
          src={`data:image/png;base64,${image128}`}
          alt={name}
          className="h-9 w-9 rounded-full object-cover border border-slate-200"
        />
      ) : (
        <div className="h-9 w-9 rounded-full bg-slate-300 flex items-center justify-center text-xs font-semibold text-white">
          {name?.[0] ?? '?'}
        </div>
      )}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{name}</p>
        <p className="text-xs text-slate-500 truncate">{jobTitle}</p>
      </div>
      <button
        onClick={onLogout}
        className="text-xs text-slate-500 hover:text-red-600"
      >
        Logout
      </button>
    </div>
  );
};
