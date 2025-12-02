import { NextResponse } from 'next/server';
import { odooJsonApi } from '@/lib/odoo';

export async function GET() {
  try {
    const data = await odooJsonApi('/med_goals/api/my-goals', {});
    return NextResponse.json(data);
  } catch (err: any) {
    console.error('MyGoals API error:', err);
    return NextResponse.json(
      { status: 'error', message: err.message || 'Unexpected error' },
      { status: 500 }
    );
  }
}
