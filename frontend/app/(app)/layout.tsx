import type { Metadata } from "next";

import { AuthGuard } from "@/components/auth/AuthGuard";
import { DemoBanner } from "@/components/shared/DemoBanner";
import { DisclaimerBanner } from "@/components/shared/DisclaimerBanner";
import { Footer } from "@/components/shared/Footer";
import { Header } from "@/components/shared/Header";

// In-app pages are private; keep them out of search indexes.
export const metadata: Metadata = {
  robots: { index: false },
};

// Shell for all in-app pages. AuthGuard redirects unauthenticated users to /login.
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="flex min-h-screen flex-col">
        <Header />
        <main id="main" className="mx-auto w-full max-w-6xl flex-1 space-y-6 px-4 py-6 sm:px-6">
          <DemoBanner />
          {children}
          <DisclaimerBanner />
        </main>
        <Footer />
      </div>
    </AuthGuard>
  );
}
