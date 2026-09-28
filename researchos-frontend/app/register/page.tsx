"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { ApiError, Role } from "@/lib/api";
import { Button, ErrorText, Field, Input } from "@/components/ui";

const ROLES: { value: Role; label: string; blurb: string }[] = [
  { value: "student", label: "Student", blurb: "Seeking mentorship and running your first projects." },
  { value: "researcher", label: "Researcher", blurb: "Managing one or more independent projects." },
  { value: "mentor", label: "Mentor", blurb: "Advising students and researchers." },
];

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [institution, setInstitution] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("student");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await register({ email, password, full_name: fullName, role, institution: institution || undefined });
      router.push("/workspaces");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-paper px-6 py-12">
      <div className="w-full max-w-md">
        <Link href="/login" className="mb-8 block font-serif text-xl text-navy">
          ResearchOS
        </Link>
        <h1 className="font-serif text-2xl text-ink">Create your account</h1>
        <p className="mt-1.5 text-sm text-slate">Set up your workspace in under a minute.</p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <Field label="Full name">
            <Input required value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Ada Researcher" />
          </Field>
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
          <Field label="Institution" hint="Optional">
            <Input value={institution} onChange={(e) => setInstitution(e.target.value)} placeholder="State University" />
          </Field>
          <Field label="Password" hint="At least 8 characters, with a letter and a number.">
            <Input
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </Field>

          <div>
            <span className="mb-1.5 block text-sm font-medium text-ink-soft">I am a…</span>
            <div className="grid grid-cols-3 gap-2">
              {ROLES.map((r) => (
                <button
                  type="button"
                  key={r.value}
                  onClick={() => setRole(r.value)}
                  className={`rounded-md border px-3 py-2 text-left text-sm transition-colors ${
                    role === r.value
                      ? "border-navy bg-navy-tint text-navy"
                      : "border-slate-light bg-white text-ink-soft hover:bg-paper-dim"
                  }`}
                >
                  <div className="font-medium">{r.label}</div>
                </button>
              ))}
            </div>
            <p className="mt-1.5 text-xs text-slate">{ROLES.find((r) => r.value === role)?.blurb}</p>
          </div>

          <ErrorText>{error}</ErrorText>

          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? "Creating account…" : "Create account"}
          </Button>
        </form>

        <p className="mt-6 text-sm text-slate">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-navy hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
