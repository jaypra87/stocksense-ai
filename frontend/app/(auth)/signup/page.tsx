import type { Metadata } from "next";

import { AuthForm } from "@/components/auth/AuthForm";

export const metadata: Metadata = {
  title: "Save your account",
  robots: { index: false },
};

export default function SignupPage() {
  return <AuthForm mode="signup" />;
}
