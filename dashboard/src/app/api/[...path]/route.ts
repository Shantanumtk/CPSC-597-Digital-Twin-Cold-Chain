import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.API_URL || 'http://state-engine.coldchain.svc.cluster.local';

export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const path = params.path.join('/');
  const searchParams = request.nextUrl.searchParams.toString();
  const url = `${API_URL}/${path}${searchParams ? '?' + searchParams : ''}`;

  try {
    const res = await fetch(url, { cache: 'no-store' });
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('API proxy error:', error);
    return NextResponse.json({ error: 'API request failed' }, { status: 500 });
  }
}