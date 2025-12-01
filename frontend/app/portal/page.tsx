import { getDashboardData } from '@/lib/odoo';
import Link from 'next/link';
import './dashboard.css';

export default async function DashboardPage() {
  const data = await getDashboardData();

  if (!data) {
    return <div className="p-8 text-center text-gray-500">Cargando dashboard...</div>;
  }

  const { employee, last_cycle, my_score, top_performers } = data;

  const getPercent = (val: number) => Math.min((val / 10) * 100, 100);

  return (
    <div className="dash-container">
      <header className="dash-header">
        <div className="welcome-text">
          <h1>Bienvenido, {employee.name.split(' ')[0]}</h1>
          <p className="subtitle">
            {employee.job_title} • {employee.med_area?.name || 'Área General'}
          </p>
        </div>
        {last_cycle && (
            <div className="cycle-indicator">
                <span className="label">Ciclo Actual</span>
                <span className="value">{last_cycle.name}</span>
                <span className={`status-dot ${last_cycle.state}`}></span>
            </div>
        )}
      </header>

      <div className="kpi-grid">
        <div className="kpi-card main-score">
            <div className="kpi-icon">⭐</div>
            <div className="kpi-content">
                <span className="kpi-label">Mi Score Total</span>
                <strong className="kpi-value">{employee.last_score.toFixed(1)}</strong>
            </div>
        </div>

        <div className="kpi-card">
            <div className="kpi-icon blue">🌍</div>
            <div className="kpi-content">
                <span className="kpi-label">Ranking Global</span>
                <strong className="kpi-value">
                    {employee.rank_area > 0 ? `#${employee.rank_area}` : '-'}
                </strong>
            </div>
        </div>

        <div className="kpi-card">
            <div className="kpi-icon green">🎯</div>
            <div className="kpi-content">
                <span className="kpi-label">Ranking Especialidad</span>
                <strong className="kpi-value">
                    {employee.rank_specialty > 0 ? `#${employee.rank_specialty}` : '-'}
                </strong>
            </div>
        </div>
      </div>

      <div className="dash-main-grid">
        <div className="score-breakdown-card card">
            <h3>📊 Desglose de Rendimiento</h3>
            {my_score ? (
                <div className="breakdown-list">
                    <div className="breakdown-item">
                        <div className="bd-info">
                            <span>Metas y Objetivos</span>
                            <strong>{my_score.score_goals}</strong>
                        </div>
                        <div className="bd-bar-bg">
                            <div className="bd-bar-fill blue" style={{ width: `${getPercent(my_score.score_goals)}%` }}></div>
                        </div>
                    </div>

                    <div className="breakdown-item">
                        <div className="bd-info">
                            <span>Contribución Económica (Profit)</span>
                            <strong>{my_score.score_economic}</strong>
                        </div>
                        <div className="bd-bar-bg">
                            <div className="bd-bar-fill green" style={{ width: `${getPercent(my_score.score_economic)}%` }}></div>
                        </div>
                    </div>

                    <div className="breakdown-item">
                        <div className="bd-info">
                            <span>Productividad</span>
                            <strong>{my_score.score_productivity}</strong>
                        </div>
                        <div className="bd-bar-bg">
                            <div className="bd-bar-fill purple" style={{ width: `${getPercent(my_score.score_productivity)}%` }}></div>
                        </div>
                    </div>

                    <div className="breakdown-item">
                        <div className="bd-info">
                            <span>Calidad</span>
                            <strong>{my_score.score_quality}</strong>
                        </div>
                        <div className="bd-bar-bg">
                            <div className="bd-bar-fill orange" style={{ width: `${getPercent(my_score.score_quality)}%` }}></div>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="empty-state">
                    <p>No hay datos de evaluación para el ciclo actual.</p>
                </div>
            )}
        </div>

        <div className="top-performers-widget card">
            <div className="widget-header">
                <h3>🏆 Top Global</h3>
                <Link href="/portal/rankings" className="link-more">Ver todos</Link>
            </div>
            
            <div className="top-list">
                {top_performers.map((p, idx) => (
                    <div key={p.employee.id} className="top-item">
                        <div className={`rank-badge rank-${idx + 1}`}>#{p.rank_global}</div>
                        <div className="top-info">
                            <span className="top-name">{p.employee.name}</span>
                            <span className="top-score">{p.score_total.toFixed(1)} pts</span>
                        </div>
                    </div>
                ))}
                
                {top_performers.length === 0 && (
                    <p className="text-muted text-sm">Aún no hay rankings disponibles.</p>
                )}
            </div>
        </div>
      </div>
    </div>
  );
}