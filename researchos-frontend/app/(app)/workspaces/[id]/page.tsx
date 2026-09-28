"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, ApiError, Visibility, Workspace } from "@/lib/api";
import { Badge, Button, ErrorText, Field, Input, Spinner, Textarea } from "@/components/ui";
import { PapersTab } from "./papers-tab";
import { ActivityTab } from "./activity-tab";

const VISIBILITY_TONE: Record<Visibility, "slate" | "navy" | "ochre"> = {
  private: "slate",
  team: "navy",
  public: "ochre",
};

type Tab = "papers" | "activity";

export default function WorkspaceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("papers");
  const [isEditing, setIsEditing] = useState(false);

  async function load() {
    try {
      const ws = await api.getWorkspace(id);
      setWorkspace(ws);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't load this workspace.");
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  if (error) {
    return (
      <div className="mx-auto max-w-4xl px-8 py-10">
        <ErrorText>{error}</ErrorText>
      </div>
    );
  }

  if (!workspace) {
    return (
      <div className="flex justify-center py-24">
        <Spinner className="h-5 w-5 text-navy" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-8 py-10">
      <Link href="/workspaces" className="text-sm text-slate hover:text-navy">
        ← Workspaces
      </Link>

      {isEditing ? (
        <EditWorkspaceForm
          workspace={workspace}
          onSaved={(ws) => {
            setWorkspace(ws);
            setIsEditing(false);
          }}
          onCancel={() => setIsEditing(false)}
        />
      ) : (
        <div className="mt-3 flex items-start justify-between">
          <div>
            <h1 className="font-serif text-3xl text-ink">{workspace.title}</h1>
            <div className="mt-2 flex items-center gap-2 text-sm text-slate">
              {workspace.domain && <span>{workspace.domain}</span>}
              <Badge tone={VISIBILITY_TONE[workspace.visibility]}>{workspace.visibility}</Badge>
            </div>
            {workspace.description && <p className="mt-3 max-w-xl text-sm text-ink-soft">{workspace.description}</p>}
          </div>
          <Button variant="secondary" onClick={() => setIsEditing(true)}>
            Edit
          </Button>
        </div>
      )}

      <div className="mt-8 flex gap-1 border-b border-slate-light">
        {(["papers", "activity"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm font-medium capitalize transition-colors ${
              tab === t ? "border-ochre text-ink" : "border-transparent text-slate hover:text-ink-soft"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="mt-6">
        {tab === "papers" && <PapersTab workspaceId={workspace.id} />}
        {tab === "activity" && <ActivityTab workspaceId={workspace.id} />}
      </div>
    </div>
  );
}

function EditWorkspaceForm({
  workspace,
  onSaved,
  onCancel,
}: {
  workspace: Workspace;
  onSaved: (ws: Workspace) => void;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState(workspace.title);
  const [domain, setDomain] = useState(workspace.domain ?? "");
  const [description, setDescription] = useState(workspace.description ?? "");
  const [visibility, setVisibility] = useState<Visibility>(workspace.visibility);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const updated = await api.updateWorkspace(workspace.id, { title, domain, description, visibility });
      onSaved(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't save changes.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-4 space-y-4 rounded-lg border border-slate-light bg-white p-6">
      <Field label="Title">
        <Input required value={title} onChange={(e) => setTitle(e.target.value)} />
      </Field>
      <Field label="Research domain">
        <Input value={domain} onChange={(e) => setDomain(e.target.value)} />
      </Field>
      <Field label="Description">
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
          {isSubmitting ? "Saving…" : "Save changes"}
        </Button>
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
