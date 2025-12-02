  import { getEmployees, getAreas, getSpecialties } from '@/lib/odoo';
  import Link from 'next/link';
  import FilterBar from '../components/FilterBar';
  import './employees.css';

  export default async function EmployeesPage({ searchParams }: { searchParams: Promise<{ area_id?: string; specialty_id?: string }> }) {
    const { area_id, specialty_id } = await searchParams;

    const areaId = area_id ? parseInt(area_id) : undefined;
    const specialtyId = specialty_id ? parseInt(specialty_id) : undefined;

    // Carga paralela de datos
    const [employees, areas, specialties] = await Promise.all([
      getEmployees({ area_id: areaId, specialty_id: specialtyId }),
      getAreas(),
      getSpecialties() // Traemos todas para que el filtro las gestione en cliente
    ]);

    return (
      <div className="emp-container">
        <header className="emp-header">
          <div>
            <h1>Directorio de Empleados</h1>
            <p>Sincronizado con Odoo HR en tiempo real.</p>
          </div>
          <div className="emp-count">
            <span>{employees.length} Activos</span>
          </div>
        </header>

        {/* BARRA DE FILTROS */}
        <FilterBar 
          areas={areas} 
          specialties={specialties} 
          basePath="/portal/employees" 
        />

        <div className="emp-card">
          <div className="emp-table-wrapper">
            <table className="emp-table">
              <thead>
                <tr>
                  <th>Empleado</th>
                  <th>Cargo</th>
                  <th>Departamento / Área</th>
                  <th>Acción</th>
                </tr>
              </thead>
              <tbody>
                {employees.map((emp) => (
                  <tr key={emp.id}>
                    <td>
                      <div className="emp-profile">
                        {emp.avatar_128 ? (
                          <img 
                            src={`data:image/png;base64,${emp.avatar_128}`} 
                            alt={emp.name} 
                            className="emp-avatar-img"
                          />
                        ) : (
                          <div className="emp-avatar">
                            {emp.name.charAt(0).toUpperCase()}
                          </div>
                        )}
                        <div className="emp-info-col">
                          <span className="emp-name">{emp.name}</span>
                          <small className="text-muted">{emp.work_email || ''}</small>
                        </div>
                      </div>
                    </td>
                    <td>
                      {emp.job_title || <span className="text-muted">Sin cargo</span>}
                    </td>
                    <td>
                      <div className="dept-info">
                          {emp.med_area_id ? (
                            <span className="dept-badge">{emp.med_area_id.display_name}</span>
                          ) : (
                            <span className="text-muted">Sin Área</span>
                          )}
                          {emp.med_specialty_id && (
                            <small className="spec-text">{emp.med_specialty_id.display_name}</small>
                          )}
                      </div>
                    </td>
                    <td>
                      <Link href={`/portal/employees/${emp.id}`} className="btn-view">
                        Ver Perfil
                      </Link>
                    </td>
                  </tr>
                ))}
                
                {employees.length === 0 && (
                  <tr>
                    <td colSpan={4} className="emp-empty">
                      No se encontraron empleados con los filtros seleccionados.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }