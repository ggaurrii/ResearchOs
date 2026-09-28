"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/auth-context";
import { Spinner } from "@/components/ui";

function NavItem({ href, label, disabled }: { href: string; label: string; disabled?: boolean }) {
  if (disabled) {
    return (
      <span className="flex items-center justify-between rounded-md px-3 py-2 text-sm text-white/35">
        {label}
        <span className="rounded-full bg-white/10 px-2 py-0.5 text-[10px] tracking-wide text-white/50">SOON</span>
      </span>
    );
  }
  return (
    <Link href={href} className="block rounded-md px-3 py-2 text-sm text-white/85 hover:bg-white/10">
      {label}
    </Link>
  );
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) router.replace("/login");
  }, [isLoading, user, router]);

  if (isLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-paper">
        <Spinner className="h-6 w-6 text-navy" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-paper">
      <aside className="flex w-60 shrink-0 flex-col justify-between bg-navy px-4 py-6">
        <div>
          <Link href="/workspaces" className="mb-8 block px-3 font-serif text-lg text-white">
            ResearchOS
          </Link>
          <nav className="space-y-1">
            <NavItem href="/workspaces" label="Workspaces" />
            <NavItem href="/mentors" label="Mentors" disabled />
            <NavItem href="/feed" label="Feed" disabled />
          </nav>
        </div>

        <div className="border-t border-white/10 pt-4">
          <div className="px-3">
            <p className="truncate text-sm font-medium text-white">{user.full_name}</p>
            <p className="truncate text-xs text-white/50">{user.email}</p>
          </div>
          <button
            onClick={() => logout().then(() => router.push("/login"))}
            className="mt-2 w-full rounded-md px-3 py-2 text-left text-sm text-white/70 hover:bg-white/10"
          >
            Sign out
          </button>
        </div>
      </aside>

      <main className="min-w-0 flex-1">{children}</main>
    </div>
  );
}
