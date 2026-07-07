const UPSTREAM_ORIGIN = "https://recova-debt-brain-lab.vercel.app";

function corsHeaders(request) {
  const origin = request.headers.get("Origin") || "*";
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "GET,HEAD,POST,OPTIONS",
    "Access-Control-Allow-Headers":
      request.headers.get("Access-Control-Request-Headers") ||
      "authorization,content-type,mcp-session-id,mcp-protocol-version",
    "Access-Control-Expose-Headers":
      "mcp-session-id,mcp-protocol-version,x-recova-edge",
    "Access-Control-Max-Age": "86400",
    Vary: "Origin",
  };
}

export default {
  async fetch(request) {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(request) });
    }

    const incomingUrl = new URL(request.url);
    const upstreamUrl = new URL(
      incomingUrl.pathname + incomingUrl.search,
      UPSTREAM_ORIGIN,
    );
    const headers = new Headers(request.headers);
    headers.delete("host");
    headers.set("x-forwarded-host", incomingUrl.host);
    headers.set("x-recova-edge", "cloudflare-worker");

    const init = {
      method: request.method,
      headers,
      redirect: "manual",
    };
    if (request.method !== "GET" && request.method !== "HEAD") {
      init.body = request.body;
    }

    const upstreamResponse = await fetch(upstreamUrl.toString(), init);
    const responseHeaders = new Headers(upstreamResponse.headers);
    for (const [key, value] of Object.entries(corsHeaders(request))) {
      responseHeaders.set(key, value);
    }
    responseHeaders.set("x-recova-edge", "cloudflare-worker");

    return new Response(upstreamResponse.body, {
      status: upstreamResponse.status,
      statusText: upstreamResponse.statusText,
      headers: responseHeaders,
    });
  },
};
