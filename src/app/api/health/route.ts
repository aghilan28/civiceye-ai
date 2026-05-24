import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export function GET() {
  return NextResponse.json({
    status: "ok",
    service: "civiceye-web",
    version: process.env.npm_package_version ?? "0.1.0",
    apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL ?? null,
    realtimeUrlConfigured: Boolean(process.env.NEXT_PUBLIC_REALTIME_URL),
    aiInferenceUrlConfigured: Boolean(process.env.NEXT_PUBLIC_AI_INFERENCE_URL),
    checkedAt: new Date().toISOString()
  });
}
