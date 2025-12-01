import { ScoreHistoryRecord, PerformanceLog } from '@/lib/odoo';

// Gráfico de Línea para Historial de Scores
export function ScoreEvolutionChart({ history }: { history: ScoreHistoryRecord[] }) {
  if (!history || history.length < 2) {
    return <div className="chart-placeholder">Se necesitan al menos 2 evaluaciones para mostrar tendencia.</div>;
  }

  // Ordenamos cronológicamente (antiguo -> nuevo)
  const data = [...history].sort((a, b) => new Date(a.create_date).getTime() - new Date(b.create_date).getTime());
  
  const width = 600;
  const height = 250;
  const padding = 40;
  
  const maxScore = 10;
  const minScore = 0;

  // Escalas
  const getX = (index: number) => padding + (index / (data.length - 1)) * (width - padding * 2);
  const getY = (val: number) => height - padding - (val / maxScore) * (height - padding * 2);

  // Construir Path de la línea
  const pathD = data.map((d, i) => 
    `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(d.score_total)}`
  ).join(' ');

  // Área sombreada bajo la línea
  const areaD = `${pathD} L ${getX(data.length - 1)} ${height - padding} L ${getX(0)} ${height - padding} Z`;

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="chart-svg">
      {/* Ejes y Grid */}
      {[0, 2.5, 5, 7.5, 10].map(val => (
        <g key={val}>
          <line x1={padding} y1={getY(val)} x2={width - padding} y2={getY(val)} stroke="#e2e8f0" strokeDasharray="4" />
          <text x={padding - 10} y={getY(val) + 4} textAnchor="end" fontSize="10" fill="#94a3b8">{val}</text>
        </g>
      ))}

      {/* Gráfico */}
      <path d={areaD} fill="rgba(59, 130, 246, 0.1)" />
      <path d={pathD} fill="none" stroke="#3b82f6" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />

      {/* Puntos */}
      {data.map((d, i) => (
        <g key={d.id} className="chart-point-group">
          <circle cx={getX(i)} cy={getY(d.score_total)} r="5" fill="white" stroke="#3b82f6" strokeWidth="2" />
          <g className="chart-tooltip">
             <rect x={getX(i) - 40} y={getY(d.score_total) - 35} width="80" height="25" rx="4" fill="#1e293b" />
             <text x={getX(i)} y={getY(d.score_total) - 18} textAnchor="middle" fill="white" fontSize="11">
               {d.score_total.toFixed(2)} pts
             </text>
          </g>
          {/* Etiqueta Eje X (Fecha) */}
          <text x={getX(i)} y={height - 10} textAnchor="middle" fontSize="10" fill="#64748b">
            {d.create_date.split('-')[1]}/{d.create_date.split('-')[0].slice(2)}
          </text>
        </g>
      ))}
    </svg>
  );
}

// Gráfico de Barras Dispersas para Performance Logs
export function LogsActivityChart({ logs }: { logs: PerformanceLog[] }) {
    if (!logs || logs.length === 0) return null;

    // Agrupar logs por fecha (día)
    const logsByDate: Record<string, number> = {};
    logs.forEach(l => {
        const date = l.date.split(' ')[0]; // YYYY-MM-DD
        logsByDate[date] = (logsByDate[date] || 0) + 1;
    });

    const dates = Object.keys(logsByDate).sort().slice(-14); // Últimos 14 días con actividad
    const maxCount = Math.max(...Object.values(logsByDate));

    return (
        <div className="activity-heatmap">
            {dates.map(date => {
                const count = logsByDate[date];
                const heightPct = Math.max((count / maxCount) * 100, 10); // Mínimo 10% altura visual
                return (
                    <div key={date} className="activity-bar-col">
                        <div className="activity-bar" style={{ height: `${heightPct}%` }} title={`${count} logs`}></div>
                        <span className="activity-date">{date.slice(5)}</span>
                    </div>
                )
            })}
             {dates.length === 0 && <p>No hay actividad reciente.</p>}
        </div>
    )
}