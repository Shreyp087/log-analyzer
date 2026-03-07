import type { Metadata } from "next";
import { IBM_Plex_Mono, Space_Grotesk } from "next/font/google";
import Script from "next/script";
import type { ReactNode } from "react";

import "./globals.css";

const heading = Space_Grotesk({
  subsets: ["latin"],
  weight: ["500", "700"],
  variable: "--font-heading"
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-mono"
});

export const metadata: Metadata = {
  title: "Log Analyzer",
  description: "Frontend shell for log ingestion, anomaly detection, and reporting."
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className={`${heading.variable} ${mono.variable}`}>
        <Script id="root-auth-redirect" strategy="beforeInteractive">
          {`
            (function () {
              try {
                if (window.location.pathname !== "/") return;
                var token = localStorage.getItem("log_analyzer_access_token");
                if (!token) return;
                var cookieName = "log_analyzer_access_token=";
                var hasCookie = document.cookie.split("; ").some(function (chunk) {
                  return chunk.indexOf(cookieName) === 0;
                });
                if (!hasCookie) {
                  document.cookie =
                    "log_analyzer_access_token=" +
                    encodeURIComponent(token) +
                    "; Path=/; Max-Age=604800; SameSite=Lax";
                }
                window.location.replace("/dashboard");
              } catch (_err) {}
            })();
          `}
        </Script>
        {children}
      </body>
    </html>
  );
}
