"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

type Feed = { sources: { id: string; version: string; retrievedAt: string | null }[] };

export default function ReleaseFeed() {
  const router = useRouter();
  const fingerprint = useRef<string | null>(null);
  const [status, setStatus] = useState("Checking releases…");

  useEffect(() => {
    const controller = new AbortController();
    let pending = false;
    async function check() {
      if (pending || document.hidden) return;
      pending = true;
      try {
        const response = await fetch("/api/releases", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Unavailable");
        const { sources } = await response.json() as Feed;
        const version = sources.map(({id, version}) => `${id}:${version}`).sort().join("|");
        if (fingerprint.current && fingerprint.current !== version) router.refresh();
        fingerprint.current = version;
        const latest = sources.flatMap(({retrievedAt}) => retrievedAt ? [retrievedAt] : []).sort().at(-1);
        setStatus(latest ? `Last release retrieved ${latest.slice(0, 10)} UTC` : "Awaiting source releases");
      } catch {
        if (!controller.signal.aborted) setStatus("Release check unavailable");
      } finally {
        pending = false;
      }
    }
    void check();
    const timer = window.setInterval(check, 60_000);
    document.addEventListener("visibilitychange", check);
    return () => {
      controller.abort();
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", check);
    };
  }, [router]);

  return <span className="release-status" role="status">{status}</span>;
}
