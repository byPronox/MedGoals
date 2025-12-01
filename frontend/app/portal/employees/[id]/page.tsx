import { getEmployeeDetail, getMedGoalsEmployeeDetail } from '@/lib/odoo';
import Link from 'next/link';
import './profile.css';

export default async function EmployeeProfile({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const employeeId = parseInt(id);

  // Llamamos en paralelo: Detalle estándar (HR) y Detalle MedGoals (Historial)
  const [emp, medGoalsData] = await Promise.all([
    getEmployeeDetail(employeeId),
    getMedGoalsEmployeeDetail(employeeId)
  ]);

  const scoreHistory = medGoalsData.score_history || [];

  if (!emp) {
    return (
      <div className="profile-container">
        <div className="card">
          <h2>Empleado no encontrado</h2>
          <Link href="/portal/employees" className="btn-back">Volver al directorio</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="profile-container">
      {/* Navegación Breadcrumb */}
      <div className="profile-nav">
        <Link href="/portal/employees">← Volver al Directorio</Link>
      </div>

      {/* Header Principal */}
      <div className="profile-header card">
        <div className="header-content">
          <div className="header-avatar-area">
            {emp.avatar_128 ? (
              <img 
                src={`data:image/png;base64,${emp.avatar_128}`} 
                alt={emp.name || 'Avatar'} 
                className="big-avatar"
              />
            ) : (
              <div className="big-avatar-placeholder">
                {(emp.name && typeof emp.name === 'string') ? emp.name[0] : '?'}
              </div>
            )}
          </div>
          <div className="header-info">
            <h1>{emp.name}</h1>
            <p className="job-title">{emp.job_title || 'Sin cargo definido'}</p>
            <div className="header-meta">
              {emp.company_id && (
                <span>🏢 {emp.company_id.display_name}</span>
              )}
              {emp.department_id && (
                <span>📍 {emp.department_id.display_name}</span>
              )}
            </div>
          </div>
          <div className="header-actions">
            {/* Si es Top Performer (viene del endpoint extendido), mostramos medalla */}
            {medGoalsData.employee?.is_top_performer && (
                <span className="status-badge gold">🏆 Top Performer</span>
            )}
            <span className="status-badge active">Activo</span>
          </div>
        </div>
      </div>

      <div className="profile-grid">
        {/* COLUMNA IZQUIERDA: Información Estática */}
        <div className="left-col">
          <div className="card section-card">
            <h3>Información de Trabajo</h3>
            <ul className="info-list">
              <li>
                <span className="label">Email:</span>
                <span className="value">{emp.work_email || '-'}</span>
              </li>
              <li>
                <span className="label">Teléfono:</span>
                <span className="value">{emp.work_phone || '-'}</span>
              </li>
              <li>
                <span className="label">Móvil:</span>
                <span className="value">{emp.mobile_phone || '-'}</span>
              </li>
              <li>
                <span className="label">Manager:</span>
                <span className="value highlight">
                  {emp.parent_id ? emp.parent_id.display_name : '-'}
                </span>
              </li>
              <li>
                <span className="label">Área:</span>
                <span className="value">{medGoalsData.employee?.med_area?.name || '-'}</span>
              </li>
              <li>
                <span className="label">Especialidad:</span>
                <span className="value">{medGoalsData.employee?.med_specialty?.name || '-'}</span>
              </li>
            </ul>
          </div>
        </div>

        {/* COLUMNA DERECHA: Dinámica */}
        <div className="right-col">
            
          {/* NUEVO SECCIÓN: HISTORIAL DE EVALUACIONES (MedGoals) */}
          {scoreHistory.length > 0 && (
            <div className="card section-card">
              <h3>Historial de Evaluaciones</h3>
              <div className="table-responsive">
                <table className="history-table">
                    <thead>
                        <tr>
                            <th>Ciclo</th>
                            <th>Total</th>
                            <th>Prod.</th>
                            <th>Calidad</th>
                            <th>Eco.</th>
                            <th>Rank</th>
                        </tr>
                    </thead>
                    <tbody>
                        {scoreHistory.map((h) => (
                            <tr key={h.id} className={h.is_top_performer ? 'row-top' : ''}>
                                <td>
                                    <div className="cycle-info">
                                        <span className="cycle-name">{h.cycle?.name || 'Ciclo'}</span>
                                        <span className="cycle-date">{h.create_date.split(' ')[0]}</span>
                                    </div>
                                </td>
                                <td>
                                    <span className="score-badge small">{h.score_total.toFixed(1)}</span>
                                </td>
                                <td>{h.score_productivity}</td>
                                <td>{h.score_quality}</td>
                                <td>{h.score_economic}</td>
                                <td className="rank-cell">
                                    <span title="Rank Global">#{h.rank_global}</span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Objetivos (Goals) */}
          {emp.goal_assignment_ids && emp.goal_assignment_ids.length > 0 && (
             <div className="card section-card">
               <h3>Objetivos Actuales</h3>
               <div className="goals-list">
                 {emp.goal_assignment_ids.map(goal => (
                   <div key={goal.id} className="goal-item">
                     <div className="goal-header">
                        <span className="goal-name">{goal.goal_id.display_name}</span>
                        <span className={`goal-pct ${goal.completion_rate >= 100 ? 'text-green' : ''}`}>
                          {Math.round(goal.completion_rate)}%
                        </span>
                     </div>
                     <div className="progress-bg">
                       <div 
                         className={`progress-fill ${goal.completion_rate >= 100 ? 'green' : ''}`} 
                         style={{width: `${Math.min(goal.completion_rate, 100)}%`}}
                       ></div>
                     </div>
                   </div>
                 ))}
               </div>
             </div>
          )}

          {/* Habilidades (Skills) */}
          {emp.employee_skill_ids && emp.employee_skill_ids.length > 0 && (
            <div className="card section-card">
              <h3>Habilidades</h3>
              <div className="skills-grid">
                {emp.employee_skill_ids.map((skill) => (
                  <div key={skill.id} className="skill-item">
                    <div className="skill-top">
                      <span className="skill-name">{skill.skill_id.display_name}</span>
                      <span className="skill-level">{skill.skill_level_id.display_name}</span>
                    </div>
                    <div className="progress-bg sm">
                      <div 
                        className="progress-fill blue" 
                        style={{ width: `${skill.level_progress}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}