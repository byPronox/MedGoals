import { getCurrentUserProfile, getMyGoals } from '@/lib/odoo';
import Link from 'next/link';
import LogoutButton from './LogoutButton'; // Importamos el componente cliente
import '../employees/[id]/profile.css'; 
import './my-goals.css'; 

export default async function MyProfilePage() {
  const emp = await getCurrentUserProfile();
  const goalsResponse = await getMyGoals();
  const myGoals = goalsResponse.records || [];

  if (!emp) {
    return <div className="p-8 text-center">No se pudo cargar el perfil del usuario.</div>;
  }

  return (
    <div className="profile-container">
      <div className="profile-header card my-profile-header">
        <div className="header-content">
          <div className="header-avatar-area">
            {emp.avatar_128 ? (
              <img 
                src={`data:image/png;base64,${emp.avatar_128}`} 
                alt={emp.name} 
                className="big-avatar"
              />
            ) : (
              <div className="big-avatar-placeholder">{emp.name[0]}</div>
            )}
          </div>
          <div className="header-info">
            <h1>Hola, {emp.name.split(' ')[0]} 👋</h1>
            <p className="job-title">{emp.job_title}</p>
            <div className="header-meta">
               <span>🏢 {emp.company_id ? emp.company_id.display_name : ''}</span>
               <span>📧 {emp.work_email}</span>
            </div>
          </div>
          <div className="header-actions">
            <span className="status-badge active">Mi Cuenta</span>
            {/* Botón de Logout añadido aquí */}
            <LogoutButton />
          </div>
        </div>
      </div>

      <div className="profile-grid">
        {/* COLUMNA IZQUIERDA: Info Personal */}
        <div className="left-col">
          <div className="card section-card">
            <h3>Mis Datos</h3>
            <ul className="info-list">
              <li><span className="label">Móvil:</span> <span className="value">{emp.mobile_phone || '-'}</span></li>
              <li><span className="label">Extensión:</span> <span className="value">{emp.work_phone || '-'}</span></li>
              <li><span className="label">Depto:</span> <span className="value">{emp.department_id ? emp.department_id.display_name : '-'}</span></li>
              <li><span className="label">Manager:</span> <span className="value highlight">{emp.parent_id ? emp.parent_id.display_name : '-'}</span></li>
            </ul>
          </div>
          
          {emp.employee_skill_ids && emp.employee_skill_ids.length > 0 && (
            <div className="card section-card">
              <h3>Mis Habilidades</h3>
              <div className="skills-grid simple">
                {emp.employee_skill_ids.map((skill) => (
                  <div key={skill.id} className="skill-chip">
                    {skill.skill_id.display_name} 
                    <span className="skill-lvl">({skill.level_progress}%)</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* COLUMNA DERECHA: MIS METAS */}
        <div className="right-col">
          <div className="card section-card">
            <div className="goals-header-row">
                <h3>🎯 Mis Objetivos Asignados</h3>
                <span className="goals-count">{myGoals.length} activos</span>
            </div>

            {myGoals.length === 0 ? (
                <div className="empty-goals">No tienes objetivos asignados actualmente.</div>
            ) : (
                <div className="my-goals-list">
                    {myGoals.map((goal) => (
                        <div key={goal.id} className="my-goal-card">
                            <div className="mg-top">
                                <span className="mg-cycle">{goal.cycle?.name || 'General'}</span>
                                <span className={`mg-state ${goal.state}`}>{goal.state.replace('_', ' ')}</span>
                            </div>
                            <h4 className="mg-title">{goal.name}</h4>
                            
                            <div className="mg-progress-area">
                                <div className="mg-labels">
                                    <span>Progreso</span>
                                    <span>{Math.round(goal.completion_rate)}%</span>
                                </div>
                                <div className="progress-bg">
                                    <div 
                                        className={`progress-fill ${goal.completion_rate >= 100 ? 'green' : ''}`}
                                        style={{width: `${Math.min(goal.completion_rate, 100)}%`}}
                                    ></div>
                                </div>
                            </div>
                            
                            <div className="mg-footer">
                                <div className="mg-metric">
                                    <small>Meta</small>
                                    <strong>{goal.target_value}</strong>
                                </div>
                                <div className="mg-metric">
                                    <small>Actual</small>
                                    <strong>{goal.actual_value}</strong>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}