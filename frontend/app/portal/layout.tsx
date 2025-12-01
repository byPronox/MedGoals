import Link from 'next/link';
import type { ReactNode } from 'react';
import { getCurrentUserProfile } from '@/lib/odoo';
import './portal.css'; 

export default async function PortalLayout({ children }: { children: ReactNode }) {
  const user = await getCurrentUserProfile();

  return (
    <div className="portal-layout">
      <aside className="portal-sidebar">
        <div className="portal-brand">
          <span className="portal-logo">MG</span>
          <span className="portal-title">MED-GOALS</span>
        </div>
        
        <nav className="portal-nav">
          <Link href="/portal" className="nav-item">Dashboard</Link>
          <Link href="/portal/employees" className="nav-item">Employees</Link>
          <Link href="/portal/rankings" className="nav-item">Rankings</Link>
          <Link href="/portal/history" className="nav-item">Activity Logs</Link>
        </nav>

        <div className="portal-user-footer">
            {user ? (
                <Link href="/portal/me" className="user-profile-link">
                    <div className="user-avatar-circle">
                        {user.avatar_128 ? (
                            <img 
                                src={`data:image/png;base64,${user.avatar_128}`} 
                                alt={user.name} 
                            />
                        ) : (
                            <span>{user.name.charAt(0)}</span>
                        )}
                    </div>
                    <div className="user-info-mini">
                        <span className="user-name">{user.name}</span>
                        <span className="user-role">{user.job_title || 'Employee'}</span>
                    </div>
                </Link>
            ) : (
                <div className="user-loading">Cargando perfil...</div>
            )}
        </div>
      </aside>
      <main className="portal-main">{children}</main>
    </div>
  );
}