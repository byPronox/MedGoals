import { NextRequest, NextResponse } from 'next/server';
import { odooJsonApi } from '@/lib/odoo';

export async function GET(req: NextRequest) {
  try {
    const cycleId = req.nextUrl.searchParams.get('cycle_id');
    const payload = cycleId ? { cycle_id: Number(cycleId) } : {};

    const data = await odooJsonApi('/med_goals/api/top_performers', payload);

    return NextResponse.json(data);
  } catch (err: any) {
    console.error('Rankings API error:', err);
    return NextResponse.json(
      { status: 'error', message: err.message || 'Unexpected error' },
      { status: 500 }
    );
  }
}
