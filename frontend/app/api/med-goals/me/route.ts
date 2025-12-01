import { NextRequest, NextResponse } from 'next/server';
import { odooJsonRpc } from '@/lib/odoo';

export async function GET(_req: NextRequest) {
  try {
    const result = await odooJsonRpc('/med_goals/api/my_goals', {});

    if (!result || result.status !== 'ok') {
      return NextResponse.json(
        result || { status: 'error', message: 'Unknown error from Odoo' },
        { status: 400 }
      );
    }

    return NextResponse.json(result);
  } catch (err: any) {
    console.error('my-goals route error', err);
    return NextResponse.json(
      { status: 'error', message: err.message || 'Internal error' },
      { status: 500 }
    );
  }
}
