'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { Employee } from '@/lib/odoo';

export default function EmployeeSelector({ employees }: { employees: Employee[] }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const currentId = searchParams.get('employee_id');

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    if (val) {
      router.push(`/portal/history?employee_id=${val}`);
    } else {
      router.push(`/portal/history`);
    }
  };

  return (
    <div className="selector-container">
      <label htmlFor="emp-select" className="selector-label">Analizar Empleado:</label>
      <div className="select-wrapper">
        <select 
          id="emp-select"
          className="emp-select"
          value={currentId || ''}
          onChange={handleChange}
        >
          <option value="">-- Seleccionar Empleado --</option>
          {employees.map(emp => (
            <option key={emp.id} value={emp.id}>
              {emp.name} — {emp.job_title || 'N/A'}
            </option>
          ))}
        </select>
        <div className="select-arrow">▼</div>
      </div>
    </div>
  );
}