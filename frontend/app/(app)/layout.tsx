import { AuthGuard } from "@/components/auth/AuthGuard";
import { DemoBanner } from "@/components/shared/DemoBanner";
import { DisclaimerBanner } from "@/components/shared/DisclaimerBanner";
import { Header } from "@/components/shared/Header";

// Shell for all in-app pages. AuthGuard redirects unauthenticated users to /login.
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <div className="min-h-screen">
        <Header />
        <main className="mx-auto max-w-6xl space-y-6 px-4 py-6">
          <DemoBanner />
          {children}
          <DisclaimerBanner />
        </main>
      </div>
    </AuthGuard>
  );
}
