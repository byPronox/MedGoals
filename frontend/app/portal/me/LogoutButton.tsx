'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LogoutButton() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleLogout = async () => {
    // Confirmación opcional para evitar clicks accidentales
    if (!confirm("¿Estás seguro que deseas cerrar sesión?")) return;

    setLoading(true);
    try {
      const res = await fetch('/api/session/logout', {
        method: 'POST',
      });

      if (res.ok) {
        router.replace('/login');
        router.refresh(); 
      } else {
        alert("Error al intentar cerrar sesión.");
      }
    } catch (e) {
      console.error("Logout error", e);
      alert("Error de conexión al cerrar sesión.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <button 
      onClick={handleLogout} 
      disabled={loading}
      className="btn-logout"
      title="Salir del sistema"
    >
      {loading ? 'Saliendo...' : 'Cerrar Sesión'}
    </button>
  );
}