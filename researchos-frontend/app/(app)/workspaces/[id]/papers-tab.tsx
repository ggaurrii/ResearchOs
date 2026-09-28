"use client";

import { ChangeEvent, FormEvent, useEffect, useRef, useState } from "react";
import { api, ApiError, LiteratureSearchResult, Paper } from "@/lib/api";
import { Badge, Button, Card, EmptyState, ErrorText, Input, Spinner } from "@/components/ui";

export function PapersTab({ workspaceId }: { workspaceId: string }) {
  const [papers, setPapers] = useState<Paper[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);

  async function loadPapers() {
    try {
      const page = await api.listPapers(workspaceId);
      setPapers(page.results);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't load papers.");
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadPapers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspaceId]);

  async function handleUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    setError(null);
    try {
      const paper = await api.uploadPaper(workspaceId, file);
      setPapers((prev) => (prev ? [paper, ...prev] : [paper]));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't upload that file.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  return (
    <div className="space-y-8">
      <LiteratureSearch
        workspaceId={workspaceId}
        onPaperAdded={(paper) => setPapers((prev) => (prev ? [paper, ...prev] : [paper]))}
      />

      <div>
        <div className="flex items-center justify-between">
          <h2 className="font-serif text-lg text-ink">Papers in this workspace</h2>
          <div>
            <input ref={fileInputRef} type="file" accept="application/pdf" className="hidden" onChange={handleUpload} />
            <Button variant="secondary" onClick={() => fileInputRef.current?.click()} disabled={isUploading}>
              {isUploading ? "Uploading…" : "Upload PDF"}
            </Button>
          </div>
        </div>

        <div className="mt-4">
          <ErrorText>{error}</ErrorText>

          {papers === null && !error && (
            <div className="flex justify-center py-10">
              <Spinner className="h-5 w-5 text-navy" />
            </div>
          )}

          {papers !== null && papers.length === 0 && (
            <EmptyState
              title="No papers yet"
              body="Search external literature above, or upload a PDF you already have access to."
            />
          )}

          <ul className="space-y-2">
            {papers?.map((paper) => (
              <li key={paper.id}>
                <Card className="px-4 py-3">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <p className="truncate font-medium text-ink">{paper.title}</p>
                      <p className="mt-0.5 truncate text-xs text-slate">
                        {paper.authors && paper.authors.length > 0 ? paper.authors.join(", ") + " · " : ""}
                        {paper.publication_year ?? ""}
                      </p>
                    </div>
                    <Badge tone="slate">{paper.source}</Badge>
                  </div>
                </Card>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

function LiteratureSearch({
  workspaceId,
  onPaperAdded,
}: {
  workspaceId: string;
  onPaperAdded: (paper: Paper) => void;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<LiteratureSearchResult[] | null>(null);
  const [sourcesFailed, setSourcesFailed] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [addingKey, setAddingKey] = useState<string | null>(null);

  async function handleSearch(e: FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setIsSearching(true);
    setError(null);
    setResults(null);
    try {
      const keywords = query
        .split(",")
        .map((k) => k.trim())
        .filter(Boolean);
      const resp = await api.searchLiterature(workspaceId, keywords);
      setResults(resp.results);
      setSourcesFailed(resp.sources_failed);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.code === "UPSTREAM_SOURCE_ERROR"
            ? "None of the literature sources responded. Try again shortly, or add a paper manually below."
            : err.message
          : "Search failed."
      );
    } finally {
      setIsSearching(false);
    }
  }

  async function handleAdd(result: LiteratureSearchResult) {
    const key = result.doi ?? result.title;
    setAddingKey(key);
    try {
      const paper = await api.addPaper(workspaceId, {
        title: result.title,
        authors: result.authors,
        doi: result.doi ?? undefined,
        source: result.source,
        publication_year: result.year ?? undefined,
        abstract: result.abstract_snippet ?? undefined,
      });
      onPaperAdded(paper);
      setResults((prev) => prev?.filter((r) => (r.doi ?? r.title) !== key) ?? null);
    } catch {
      // Leave the result in the list; the person can retry.
    } finally {
      setAddingKey(null);
    }
  }

  return (
    <div>
      <h2 className="font-serif text-lg text-ink">Search literature</h2>
      <form onSubmit={handleSearch} className="mt-3 flex gap-2">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="vision transformer, MRI segmentation"
        />
        <Button type="submit" disabled={isSearching}>
          {isSearching ? "Searching…" : "Search"}
        </Button>
      </form>
      <p className="mt-1.5 text-xs text-slate">Separate multiple keywords with commas.</p>

      <div className="mt-4">
        <ErrorText>{error}</ErrorText>

        {sourcesFailed.length > 0 && !error && (
          <p className="mb-3 text-xs text-slate">
            No results from: {sourcesFailed.join(", ")}. Showing results from the remaining sources.
          </p>
        )}

        {results && results.length === 0 && !error && (
          <p className="py-4 text-sm text-slate">No results. Try different or broader keywords.</p>
        )}

        <ul className="space-y-2">
          {results?.map((result) => {
            const key = result.doi ?? result.title;
            return (
              <li key={key}>
                <Card className="px-4 py-3">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <p className="truncate font-medium text-ink">{result.title}</p>
                      <p className="mt-0.5 truncate text-xs text-slate">
                        {result.authors.length > 0 ? result.authors.join(", ") + " · " : ""}
                        {result.year ?? ""} {result.venue ? `· ${result.venue}` : ""}
                      </p>
                      {result.abstract_snippet && (
                        <p className="mt-1.5 line-clamp-2 text-xs text-ink-soft">{result.abstract_snippet}</p>
                      )}
                    </div>
                    <Button
                      variant="secondary"
                      onClick={() => handleAdd(result)}
                      disabled={addingKey === key}
                      className="shrink-0"
                    >
                      {addingKey === key ? "Adding…" : "Add"}
                    </Button>
                  </div>
                </Card>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
