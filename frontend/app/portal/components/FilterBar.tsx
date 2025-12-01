'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { Area, Specialty } from '@/lib/odoo';

interface FilterBarProps {
  areas: Area[];
  specialties: Specialty[]; 
  showSpecialty?: boolean;  
  basePath: string; 
}

export default function FilterBar({ areas, specialties, showSpecialty = true, basePath }: FilterBarProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const selectedArea = searchParams.get('area_id') || '';
  const selectedSpecialty = searchParams.get('specialty_id') || '';

  // CORRECCIÓN: Filtramos usando s.area.id porque area es un objeto {id, name}
  const visibleSpecialties = selectedArea 
    ? specialties.filter(s => s.area && s.area.id === parseInt(selectedArea))
    : [];

  const handleAreaChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const areaId = e.target.value;
    const params = new URLSearchParams(searchParams.toString());
    
    if (areaId) {
      params.set('area_id', areaId);
    } else {
      params.delete('area_id');
    }
    
    // Al cambiar área, reseteamos especialidad
    params.delete('specialty_id');
    
    router.push(`${basePath}?${params.toString()}`);
  };

  const handleSpecialtyChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const specId = e.target.value;
    const params = new URLSearchParams(searchParams.toString());
    
    if (specId) {
      params.set('specialty_id', specId);
    } else {
      params.delete('specialty_id');
    }
    
    router.push(`${basePath}?${params.toString()}`);
  };

  return (
    <div className="filter-bar">
      <div className="filter-group">
        <label>Filtrar por Área:</label>
        <select value={selectedArea} onChange={handleAreaChange} className="filter-select">
          <option value="">-- Todas las Áreas --</option>
          {areas.map(area => (
            <option key={area.id} value={area.id}>{area.name}</option>
          ))}
        </select>
      </div>

      {showSpecialty && (
        <div className="filter-group">
          <label>Especialidad:</label>
          <select 
            value={selectedSpecialty} 
            onChange={handleSpecialtyChange} 
            className="filter-select"
            disabled={!selectedArea} // Desactivado si no hay área
          >
            <option value="">-- Todas --</option>
            {visibleSpecialties.map(spec => (
              <option key={spec.id} value={spec.id}>{spec.name}</option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}