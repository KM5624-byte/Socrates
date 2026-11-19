import "server-only";
import { snapshotResponse } from "./snapshot";

const upstream = process.env.AILEO_API_URL;

export async function api(path: string) {
  if (!upstream && process.env.VERCEL === "1") {
    return snapshotResponse(new URL(path, "https://snapshot.invalid"));
  }
  return fetch(new URL(path, upstream ?? "http://127.0.0.1:8000"), {
    cache: "no-store",
    signal: AbortSignal.timeout(8000),
  });
}
