"use client";

import { useEffect, useState } from "react";
import { ActivityEntry, api, ApiError } from "@/lib/api";
import { EmptyState, ErrorText, Spinner } from "@/components/ui";

const EVENT_LABELS: Record<string, string> = {
  workspace_created: "Workspace created",
  workspace_updated: "Workspace details updated",
  workspace_archived: "Workspace archived",
  paper_added: "Paper added",
  paper_uploaded: "Paper uploaded",
};

function describeEvent(entry: ActivityEntry): string {
  const label = EVENT_LABELS[entry.event_type] ?? entry.event_type;
  if (entry.event_type === "paper_added" && entry.event_data?.title) {
    return `${label}: “${entry.event_data.title}”`;
  }
  if (entry.event_type === "paper_uploaded" && entry.event_data?.filename) {
    return `${label}: ${entry.event_data.filename}`;
  }
  return label;
}

export function ActivityTab({ workspaceId }: { workspaceId: string }) {
  const [entries, setEntries] = useState<ActivityEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getActivity(workspaceId)
      .then((page) => setEntries(page.results))
      .catch((err) => setError(err instanceof ApiError ? err.message : "Couldn't load activity."));
  }, [workspaceId]);

  if (error) return <ErrorText>{error}</ErrorText>;

  if (entries === null) {
    return (
      <div className="flex justify-center py-10">
        <Spinner className="h-5 w-5 text-navy" />
      </div>
    );
  }

  if (entries.length === 0) {
    return <EmptyState title="No activity yet" body="Everything that happens in this workspace will show up here." />;
  }

  return (
    <ol className="space-y-0">
      {entries.map((entry) => (
        <li key={entry.id} className="relative border-l border-slate-light pb-6 pl-6 last:border-transparent last:pb-0">
          <span className="absolute -left-[5px] top-1 h-2.5 w-2.5 rounded-full bg-ochre" />
          <p className="text-sm text-ink">{describeEvent(entry)}</p>
          <p className="mt-0.5 text-xs text-slate">{new Date(entry.created_at).toLocaleString()}</p>
        </li>
      ))}
    </ol>
  );
}
