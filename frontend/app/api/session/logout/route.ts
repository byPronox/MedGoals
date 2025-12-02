import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

export async function POST() {
  const cookieStore = await cookies();
  const sessionName = process.env.SESSION_COOKIE_NAME || 'session_id';

  cookieStore.delete(sessionName);

  return NextResponse.json({ 
    status: 'ok', 
    message: 'Sesión cerrada correctamente' 
  });
}