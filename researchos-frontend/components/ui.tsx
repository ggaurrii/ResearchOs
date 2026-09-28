import Link from "next/link";
import { ButtonHTMLAttributes, InputHTMLAttributes, LabelHTMLAttributes, ReactNode, TextareaHTMLAttributes } from "react";

export function Button({
  variant = "primary",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "ghost" | "danger" }) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed";
  const variants: Record<string, string> = {
    primary: "bg-ochre text-white hover:bg-ochre-dark",
    secondary: "bg-white text-ink border border-slate-light hover:bg-paper-dim",
    ghost: "text-ink-soft hover:bg-paper-dim",
    danger: "bg-white text-danger border border-danger/30 hover:bg-danger-tint",
  };
  return <button className={`${base} ${variants[variant]} ${className}`} {...props} />;
}

export function Input({ className = "", ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={`w-full rounded-md border border-slate-light bg-white px-3 py-2 text-sm text-ink placeholder:text-slate focus:border-navy ${className}`}
      {...props}
    />
  );
}

export function Textarea({ className = "", ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={`w-full rounded-md border border-slate-light bg-white px-3 py-2 text-sm text-ink placeholder:text-slate focus:border-navy ${className}`}
      {...props}
    />
  );
}

export function Label({ className = "", ...props }: LabelHTMLAttributes<HTMLLabelElement>) {
  return <label className={`mb-1.5 block text-sm font-medium text-ink-soft ${className}`} {...props} />;
}

export function Field({ label, children, hint }: { label: string; children: ReactNode; hint?: string }) {
  return (
    <div>
      <Label>{label}</Label>
      {children}
      {hint && <p className="mt-1 text-xs text-slate">{hint}</p>}
    </div>
  );
}

export function ErrorText({ children }: { children: ReactNode }) {
  if (!children) return null;
  return (
    <div className="rounded-md border border-danger/25 bg-danger-tint px-3 py-2 text-sm text-danger">
      {children}
    </div>
  );
}

export function Card({ className = "", children }: { className?: string; children: ReactNode }) {
  return <div className={`rounded-lg border border-slate-light bg-white ${className}`}>{children}</div>;
}

export function Badge({ tone = "slate", children }: { tone?: "slate" | "navy" | "ochre" | "success"; children: ReactNode }) {
  const tones: Record<string, string> = {
    slate: "bg-paper-dim text-ink-soft",
    navy: "bg-navy-tint text-navy",
    ochre: "bg-ochre-tint text-ochre-dark",
    success: "bg-success-tint text-success",
  };
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${tones[tone]}`}>
      {children}
    </span>
  );
}

export function EmptyState({
  title,
  body,
  actionLabel,
  actionHref,
}: {
  title: string;
  body: string;
  actionLabel?: string;
  actionHref?: string;
}) {
  return (
    <div className="rounded-lg border border-dashed border-slate-light bg-white/60 px-8 py-14 text-center">
      <h3 className="font-serif text-xl text-ink">{title}</h3>
      <p className="mx-auto mt-2 max-w-sm text-sm text-slate">{body}</p>
      {actionLabel && actionHref && (
        <Link href={actionHref}>
          <Button className="mt-5">{actionLabel}</Button>
        </Link>
      )}
    </div>
  );
}

export function Spinner({ className = "" }: { className?: string }) {
  return (
    <svg className={`animate-spin ${className}`} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
      <path className="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
    </svg>
  );
}
