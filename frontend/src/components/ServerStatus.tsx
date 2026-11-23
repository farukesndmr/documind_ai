import { useEffect, useState } from "react";

import { pingServer } from "../api";
import { Icon } from "./Icon";

/** Bu süre içinde cevap gelmezse sunucunun uyandığı varsayılır. */
const SLOW_THRESHOLD_MS = 2500;

type Status = "checking" | "waking" | "ready" | "offline";

/**
 * Ücretsiz barındırmada sunucu boşta kalınca uyur ve ilk istek 30-60 sn sürer.
 * Bu bileşen o sırada kullanıcıyı bilgilendirir; sunucu hızlı cevap verirse hiç görünmez.
 */
export function ServerStatus() {
  const [status, setStatus] = useState<Status>("checking");

  useEffect(() => {
    let cancelled = false;

    const slowTimer = window.setTimeout(() => {
      if (!cancelled) {
        setStatus((current) => (current === "checking" ? "waking" : current));
      }
    }, SLOW_THRESHOLD_MS);

    void pingServer().then((ok) => {
      if (!cancelled) {
        setStatus(ok ? "ready" : "offline");
      }
    });

    return () => {
      cancelled = true;
      window.clearTimeout(slowTimer);
    };
  }, []);

  if (status === "checking" || status === "ready") {
    return null;
  }

  if (status === "offline") {
    return (
      <div className="server-banner offline" role="alert">
        <Icon name="server" size={16} />
        <span>
          The server is not responding right now. Please refresh the page in a
          minute.
        </span>
      </div>
    );
  }

  return (
    <div className="server-banner" role="status">
      <span className="server-pulse" />
      <span>
        <strong>Waking up the server…</strong> The free hosting plan sleeps
        when idle, so the first request can take up to a minute.
      </span>
    </div>
  );
}
