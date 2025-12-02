import { getRankings, EmployeeRanking, getRankingCycleInfo, getAreas } from '@/lib/odoo';
import FilterBar from '../components/FilterBar';
import './rankings.css';

function groupByArea(employees: EmployeeRanking[]) {
  const groups: Record<string, EmployeeRanking[]> = {};
  employees.forEach(emp => {
    if (emp.med_area_id) {
      const areaName = emp.med_area_id.display_name;
      if (!groups[areaName]) groups[areaName] = [];
      groups[areaName].push(emp);
    }
  });
  return groups;
}

function getDreamTeam(areaEmployees: EmployeeRanking[]) {
  const bestBySpecialty: Record<string, EmployeeRanking> = {};
  areaEmployees.forEach(emp => {
    if (!emp.med_specialty_id) return;
    const specName = emp.med_specialty_id.display_name;
    if (!bestBySpecialty[specName] || emp.last_score > bestBySpecialty[specName].last_score) {
      bestBySpecialty[specName] = emp;
    }
  });
  return Object.values(bestBySpecialty);
}

export default async function RankingsPage({ searchParams }: { searchParams: Promise<{ area_id?: string }> }) {
  const { area_id } = await searchParams;
  const areaId = area_id ? parseInt(area_id) : undefined;

  // Carga paralela: Rankings (filtrados o no), Ciclo, y Áreas para el filtro
  const [employees, cycleInfo, areas] = await Promise.all([
    getRankings(areaId),
    getRankingCycleInfo(),
    getAreas()
  ]);

  const employeesByArea = groupByArea(employees);
  const areaNames = Object.keys(employeesByArea).sort();

  return (
    <div className="rankings-container">
      <header className="rankings-header">
        <h1>🏆 Clasificación de Rendimiento</h1>
        <p>Top Performers y Dream Teams por Área</p>
      </header>

      {/* FILTRO DE ÁREA */}
      <div className="rankings-filter-wrapper">
         <FilterBar 
            areas={areas} 
            specialties={[]} // No necesitamos especialidades aquí
            showSpecialty={false} // Ocultamos el select de especialidad
            basePath="/portal/rankings" 
         />
      </div>

      {/* Solo mostramos el Podio Global si NO hay filtro de área, o si quieres verlo siempre */}
      {!areaId && (
          <section className="podium-section">
            <h2>Top Performers Globales</h2>
            <div className="podium-grid">
              {employees.slice(0, 3).map((emp, index) => (
                <div key={emp.id} className={`podium-card position-${index + 1}`}>
                  <div className="medal-icon">
                    {index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉'}
                  </div>
                  <div className="podium-avatar">
                    {emp.avatar_128 ? (
                      <img src={`data:image/png;base64,${emp.avatar_128}`} alt={emp.name} />
                    ) : (
                      <div className="avatar-placeholder">{emp.name[0]}</div>
                    )}
                  </div>
                  <div className="podium-info">
                    <h3>{emp.name}</h3>
                    <span className="score-badge">{emp.last_score.toFixed(1)} / 10</span>
                    <p className="area-text">{emp.med_area_id ? emp.med_area_id.display_name : ''}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>
      )}

      {/* AREAS LIST (Si filtro activo, solo sale 1 área) */}
      <div className="areas-grid">
        {areaNames.map(areaName => {
          const areaEmps = employeesByArea[areaName].sort((a, b) => b.rank_area - a.rank_area); 
          // Orden por ranking del area (menor es mejor)
          areaEmps.sort((a, b) => (a.rank_area || 999) - (b.rank_area || 999));
          
          const dreamTeam = getDreamTeam(areaEmps);

          return (
            <div key={areaName} className="area-wrapper">
              <div className="area-header">
                <h2>{areaName}</h2>
                <span className="badge-count">{areaEmps.length} Miembros</span>
              </div>

              <div className="area-content-split">
                
                {/* Tabla de Ranking del Área */}
                <div className="ranking-card card">
                  <h3>📊 Tabla de Posiciones</h3>
                  <table className="ranking-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Empleado</th>
                        <th>Beneficio (Eco)</th>
                        <th>Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {areaEmps.slice(0, 10).map((emp) => {
                        const ecoScore = emp.employee_score_ids?.[0]?.score_economic || 0;
                        return (
                          <tr key={emp.id} className={emp.is_top_performer ? 'highlight-row' : ''}>
                            <td className="rank-num">#{emp.rank_area}</td>
                            <td>
                              <div className="mini-profile">
                                <span className="name">{emp.name}</span>
                                <span className="spec-label">
                                  {emp.med_specialty_id ? emp.med_specialty_id.display_name : '-'}
                                </span>
                              </div>
                            </td>
                            <td>
                              <div className="eco-bar-wrapper" title={`Impacto Económico: ${ecoScore}`}>
                                <div className="eco-bar" style={{ width: `${ecoScore * 10}%` }}></div>
                              </div>
                            </td>
                            <td className="score-cell">
                              <strong>{emp.last_score.toFixed(1)}</strong>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Dream Team del Área */}
                <div className="dream-team-card card">
                  <h3>🚀 Equipo Ideal ({areaName})</h3>
                  <p className="subtitle">Los mejores de cada especialidad</p>
                  
                  <div className="team-grid">
                    {dreamTeam.map(emp => (
                      <div key={emp.id} className="team-member">
                        <div className="member-avatar">
                          {emp.avatar_128 ? (
                             <img src={`data:image/png;base64,${emp.avatar_128}`} alt={emp.name} />
                          ) : (
                             <span>{emp.name[0]}</span>
                          )}
                        </div>
                        <div className="member-info">
                          <strong>{emp.med_specialty_id ? emp.med_specialty_id.display_name : 'General'}</strong>
                          <span>{emp.name}</span>
                          <small className="dt-score">⭐ {emp.last_score.toFixed(1)}</small>
                        </div>
                      </div>
                    ))}
                    {dreamTeam.length === 0 && <p className="text-muted small">No hay suficientes datos.</p>}
                  </div>
                </div>

              </div>
            </div>
          );
        })}
      </div>
      
      {areaNames.length === 0 && (
         <div className="empty-rankings">
            <p>No se encontraron resultados para el área seleccionada.</p>
         </div>
      )}
    </div>
  );
}