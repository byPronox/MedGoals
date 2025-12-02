import {
  getEmployees,
  getMedGoalsEmployeeDetail,
  getPerformanceLogs,
  getEmployeeDetail,
  Employee,
  EmployeeDetail,
  PerformanceLog,
  ScoreHistoryRecord,
} from '@/lib/odoo';
import EmployeeSelector from './EmployeeSelector';
import { ScoreEvolutionChart, LogsActivityChart } from './Charts';
import './history.css';

export default async function ActivityHistoryPage({
  searchParams,
}: {
  searchParams?: { employee_id?: string };
}) {
  const { employee_id } = searchParams || {};

  // 1. Cargar lista de empleados para el selector
  const allEmployees = await getEmployees();

  let selectedEmployeeData: any = null;
  let scoreHistory: ScoreHistoryRecord[] = [];
  let performanceLogs: PerformanceLog[] = [];
  let empDetail: EmployeeDetail | null = null;

  // 2. Si hay un empleado seleccionado, cargar su data analítica
  if (employee_id) {
    const id = parseInt(employee_id);

    // Ejecutamos en paralelo para velocidad
    const [medGoalsData, logs, detail] = await Promise.all([
      getMedGoalsEmployeeDetail(id),
      getPerformanceLogs({ employee_id: id }),
      getEmployeeDetail(id), // Para datos básicos como avatar
    ]);

    selectedEmployeeData = medGoalsData.employee; // Datos básicos del endpoint custom
    scoreHistory = medGoalsData.score_history || [];
    performanceLogs = logs || [];
    empDetail = detail; // Datos detallados (HR)
  }

  return (
    <div className="history-container">
      <header className="history-header">
        <div className="header-text">
          <h1>Analíticas & Actividad</h1>
          <p>Explora el historial de rendimiento y logs técnicos.</p>
        </div>

        {/* Selector de Empleado */}
        <EmployeeSelector employees={allEmployees} />
      </header>

      {!employee_id ? (
        <div className="empty-selection">
          <div className="empty-icon">👈</div>
          <h2>Selecciona un empleado para ver sus analíticas</h2>
          <p>Utiliza el selector superior para cargar el reporte histórico.</p>
        </div>
      ) : (
        <div className="analytics-grid">
          {/* TARJETA RESUMEN EMPLEADO */}
          <div className="card profile-summary-card">
            <div className="summary-flex">
              <div className="summary-avatar">
                {empDetail?.avatar_128 ? (
                  <img
                    src={`data:image/png;base64,${empDetail.avatar_128}`}
                    alt="Avatar"
                  />
                ) : (
                  <span>{empDetail?.name?.[0]}</span>
                )}
              </div>
              <div className="summary-info">
                <h2>{empDetail?.name}</h2>
                <p>{empDetail?.job_title}</p>
                    <div className="badges-row">
                    <span className="badge-area">
                        {selectedEmployeeData?.med_area?.name || 'N/A'}
                    </span>
                    {selectedEmployeeData?.is_top_performer && (
                        <span className="badge-top">⭐ Top Performer</span>
                    )}
                    </div>
              </div>
              <div className="summary-kpi">
                <small>Último Score</small>
                <strong>
                  {selectedEmployeeData?.last_score?.toFixed(1) || '0.0'}
                </strong>
              </div>
            </div>
          </div>

          {/* GRÁFICO 1: EVOLUCIÓN SCORES */}
          <div className="card chart-card">
            <div className="card-header">
              <h3>📈 Evolución de Rendimiento</h3>
              <span className="subtitle">
                Histórico de puntajes totales por ciclo
              </span>
            </div>
            <div className="chart-wrapper">
              <ScoreEvolutionChart history={scoreHistory} />
            </div>
          </div>

          {/* GRÁFICO 2: ACTIVIDAD RECIENTE */}
          <div className="card activity-card">
            <div className="card-header">
              <h3>🔥 Intensidad de Actividad</h3>
              <span className="subtitle">
                Logs generados en los últimos días
              </span>
            </div>
            <LogsActivityChart logs={performanceLogs} />
          </div>

          {/* TABLA DETALLADA DE LOGS */}
          <div className="card logs-table-card full-width">
            <div className="card-header">
              <h3>📜 Registro Técnico (Logs)</h3>
              <span className="count-badge">
                {performanceLogs.length} eventos
              </span>
            </div>
            <div className="table-responsive">
              <table className="tech-table">
                <thead>
                  <tr>
                    <th>Fecha/Hora</th>
                    <th>Evento / Descripción</th>
                    <th>Métrica</th>
                    <th>Asignación Relacionada</th>
                  </tr>
                </thead>
                <tbody>
                  {performanceLogs.map((log) => (
                    <tr key={log.id}>
                      <td className="mono-font">{log.date}</td>
                      <td>
                        <span className="log-name">{log.name}</span>
                        {log.notes && (
                          <p className="log-notes">{log.notes}</p>
                        )}
                      </td>
                      <td>
                        {log.metric_value ? (
                          <span className="metric-tag">
                            {log.metric_value}
                          </span>
                        ) : (
                          <span className="text-muted">-</span>
                        )}
                      </td>
                      <td>
                        {log.assignment ? (
                          <span className="assignment-link">
                            🔗 {log.assignment.name}
                          </span>
                        ) : (
                          <span className="text-muted">-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                  {performanceLogs.length === 0 && (
                    <tr>
                      <td
                        colSpan={4}
                        className="text-center p-4"
                      >
                        No hay logs de actividad registrados.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
