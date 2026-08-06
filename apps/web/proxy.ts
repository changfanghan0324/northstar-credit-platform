import { NextRequest, NextResponse } from "next/server";

export function proxy(request: NextRequest) {
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set(
    "x-northstar-locale",
    request.nextUrl.pathname.startsWith("/zh-TW") ? "zh-Hant-TW" : "en",
  );
  return NextResponse.next({ request: { headers: requestHeaders } });
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
