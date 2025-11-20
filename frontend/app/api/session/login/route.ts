import { NextRequest, NextResponse } from 'next/server';

process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

export const runtime = 'nodejs';

const ODOO_URL = process.env.ODOO_URL!;
const ODOO_DB = process.env.ODOO_DB!;
const SESSION_COOKIE_NAME = process.env.SESSION_COOKIE_NAME || 'session_id';

export async function POST(req: NextRequest) {
  try {
    const { email, password } = await req.json();

    if (!email || !password) {
      return NextResponse.json(
        { status: 'error', message: 'Missing email or password' },
        { status: 400 }
      );
    }

    const odooRes = await fetch(`${ODOO_URL}/web/session/authenticate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'call',
        params: {
          db: ODOO_DB,
          login: email,
          password,
        },
        id: Date.now(),
      }),
    });

    const setCookieHeader = odooRes.headers.get('set-cookie') || '';

    const body = await odooRes.json().catch(() => null);

    if (!odooRes.ok || !body || (body as any).error) {
      const b: any = body;
      const message =
        b?.error?.data?.message ||
        b?.error?.message ||
        'Invalid credentials';

      return NextResponse.json(
        { status: 'error', message },
        { status: 401 }
      );
    }

    const result: any = (body as any).result;
    const uid = result?.uid;
    const user = result?.user_context || {};

    if (!uid) {
      return NextResponse.json(
        { status: 'error', message: 'Authentication failed (no uid)' },
        { status: 401 }
      );
    }

    const match = setCookieHeader.match(/session_id=([^;]+)/);
    const sessionId = match ? match[1] : null;

    if (!sessionId) {
      return NextResponse.json(
        { status: 'error', message: 'Unable to get session_id from Odoo' },
        { status: 500 }
      );
    }

    const res = NextResponse.json(
      {
        status: 'ok',
        uid,
        user,
      },
      { status: 200 }
    );

    res.cookies.set(SESSION_COOKIE_NAME, sessionId, {
      httpOnly: true,
      secure: true,
      sameSite: 'lax',
      path: '/',
    });

    return res;
  } catch (err: any) {
    console.error('Login error:', err);

    const msg =
      err?.code === 'DEPTH_ZERO_SELF_SIGNED_CERT'
        ? 'Error connecting to Odoo: self-signed TLS certificate'
        : 'Internal server error';

    return NextResponse.json(
      { status: 'error', message: msg },
      { status: 500 }
    );
  }
}
