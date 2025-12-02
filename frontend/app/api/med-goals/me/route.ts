import { NextRequest, NextResponse } from 'next/server';
import { getMyGoals } from '@/lib/odoo';

export async function GET(_req: NextRequest) {
  try {
    const result = await getMyGoals();

    if (!result || result.status !== 'ok') {
      return NextResponse.json(
        result || { status: 'error', message: 'Unknown error from Odoo' },
        { status: 400 }
      );
    }

    return NextResponse.json(result);
  } catch (err: any) {
    console.error('my-goals route error', err);

    // Si odooJsonApi hizo redirect, re-lanzamos el error para que Next lo maneje
    if (err?.digest?.startsWith?.('NEXT_REDIRECT')) {
      throw err;
    }

    return NextResponse.json(
      { status: 'error', message: err.message || 'Internal error' },
      { status: 500 }
    );
  }
}
