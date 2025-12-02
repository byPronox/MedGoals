import { NextRequest, NextResponse } from 'next/server';
import { odooJsonApi } from '@/lib/odoo';

export async function GET(req: NextRequest) {
  const assignmentId = req.nextUrl.searchParams.get('assignment_id');
  const payload: any = {};
  if (assignmentId) payload.assignment_id = Number(assignmentId);

  const { ok, status, data } = await odooJsonApi('/med_goals/api/me/logs', payload);
  if (!ok) {
    return NextResponse.json(
      { status: 'error', message: 'Failed to load logs', raw: data },
      { status: status || 500 }
    );
  }
  return NextResponse.json({ status: 'ok', ...data });
}

// POST: crea un log
export async function POST(req: NextRequest) {
  const body = await req.json();
  const { assignment_id, ...rest } = body || {};
  const payload = {
    create: true, // ojo: en TS debes usar true, aquí es ejemplo; abajo lo corrijo
  };
}
