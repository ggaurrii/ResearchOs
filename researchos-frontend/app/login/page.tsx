"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api";
import { Button, ErrorText, Field, Input } from "@/components/ui";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login(email, password);
      router.push("/workspaces");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen">
      <div className="hidden w-1/2 flex-col justify-between bg-navy px-14 py-12 text-white lg:flex">
        <span className="font-serif text-2xl">ResearchOS</span>
        <div>
          <p className="max-w-sm font-serif text-3xl leading-snug">
            One workspace for literature, collaboration, and everything in between.
          </p>
          <p className="mt-4 max-w-sm text-sm text-white/70">
            Discover papers, organize your project, and bring in mentors and
            teammates — without switching between a dozen tabs.
          </p>
        </div>
        <p className="text-xs text-white/50">Autonomous Research Laboratory Platform</p>
      </div>

      <div className="flex w-full flex-col justify-center px-8 py-12 sm:px-16 lg:w-1/2">
        <div className="mx-auto w-full max-w-sm">
          <span className="mb-10 block font-serif text-xl text-navy lg:hidden">ResearchOS</span>
          <h1 className="font-serif text-2xl text-ink">Sign in</h1>
          <p className="mt-1.5 text-sm text-slate">Pick up where you left off.</p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            <Field label="Email">
              <Input
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@university.edu"
              />
            </Field>
            <Field label="Password">
              <Input
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </Field>

            <ErrorText>{error}</ErrorText>

            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? "Signing in…" : "Sign in"}
            </Button>
          </form>

          <p className="mt-6 text-sm text-slate">
            New to ResearchOS?{" "}
            <Link href="/register" className="font-medium text-navy hover:underline">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
