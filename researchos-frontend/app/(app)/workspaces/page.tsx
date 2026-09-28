"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { api, ApiError, Visibility, Workspace } from "@/lib/api";
import { Badge, Button, EmptyState, ErrorText, Field, Input, Spinner, Textarea } from "@/components/ui";

const VISIBILITY_TONE: Record<Visibility, "slate" | "navy" | "ochre"> = {
  private: "slate",
  team: "navy",
  public: "ochre",
};

export default function WorkspacesPage() {
  const [workspaces, setWorkspaces] = useState<Workspace[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);

  async function load() {
    try {
      const page = await api.listWorkspaces();
      setWorkspaces(page.results);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't load your workspaces.");
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, []);

  return (
    <div className="mx-auto max-w-4xl px-8 py-10">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-serif text-3xl text-ink">Workspaces</h1>
          <p className="mt-1 text-sm text-slate">Every project you own or collaborate on.</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>New workspace</Button>
      </div>

      {showCreate && (
        <CreateWorkspaceForm
          onCreated={(ws) => {
            setShowCreate(false);
            setWorkspaces((prev) => (prev ? [ws, ...prev] : [ws]));
          }}
          onCancel={() => setShowCreate(false)}
        />
      )}

      <div className="mt-8">
        <ErrorText>{error}</ErrorText>

        {workspaces === null && !error && (
          <div className="flex justify-center py-16">
            <Spinner className="h-5 w-5 text-navy" />
          </div>
        )}

        {workspaces !== null && workspaces.length === 0 && (
          <EmptyState
            title="No workspaces yet"
            body="A workspace holds everything for one project — papers, notes, and the people working on it. Create your first one to get started."
            actionLabel="Create a workspace"
            actionHref="#"
          />
        )}

        <ul className="space-y-3">
          {workspaces?.map((ws) => (
            <li key={ws.id}>
              <Link
                href={`/workspaces/${ws.id}`}
                className="flex items-center justify-between rounded-lg border border-slate-light bg-white px-5 py-4 transition-colors hover:border-navy/40"
              >
                <div className="min-w-0">
                  <h2 className="truncate font-serif text-lg text-ink">{ws.title}</h2>
                  {ws.domain && <p className="mt-0.5 truncate text-sm text-slate">{ws.domain}</p>}
                </div>
                <Badge tone={VISIBILITY_TONE[ws.visibility]}>{ws.visibility}</Badge>
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function CreateWorkspaceForm({
  onCreated,
  onCancel,
}: {
  onCreated: (ws: Workspace) => void;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState("");
  const [domain, setDomain] = useState("");
  const [description, setDescription] = useState("");
  const [visibility, setVisibility] = useState<Visibility>("private");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const ws = await api.createWorkspace({
        title,
        domain: domain || undefined,
        description: description || undefined,
        visibility,
      });
      onCreated(ws);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't create the workspace.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-6 space-y-4 rounded-lg border border-slate-light bg-white p-6">
      <Field label="Title">
        <Input required value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Vision Transformers for MRI Segmentation" />
      </Field>
      <Field label="Research domain" hint="Optional">
        <Input value={domain} onChange={(e) => setDomain(e.target.value)} placeholder="Medical Imaging" />
      </Field>
      <Field label="Description" hint="Optional">
        <Textarea rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
      </Field>
      <div>
        <span className="mb-1.5 block text-sm font-medium text-ink-soft">Visibility</span>
        <div className="flex gap-2">
          {(["private", "team", "public"] as Visibility[]).map((v) => (
            <button
              type="button"
              key={v}
              onClick={() => setVisibility(v)}
              className={`rounded-md border px-3 py-1.5 text-sm capitalize transition-colors ${
                visibility === v ? "border-navy bg-navy-tint text-navy" : "border-slate-light text-ink-soft hover:bg-paper-dim"
              }`}
            >
              {v}
            </button>
          ))}
        </div>
      </div>

      <ErrorText>{error}</ErrorText>

      <div className="flex gap-2 pt-1">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Creating…" : "Create workspace"}
        </Button>
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
