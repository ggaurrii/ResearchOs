# ResearchOS Frontend

Next.js (App Router + TypeScript + Tailwind CSS v4) frontend for ResearchOS,
built against the backend in `researchos-backend.zip` — specifically
Modules 1–3 (User Management, Research Workspace, Literature Discovery).

## What's implemented

- **Auth**: register, login, JWT access token + automatic refresh-on-401,
  logout. Route-level guard redirects signed-out users to `/login` and
  signed-in users away from it.
- **Workspaces**: list, create, view, edit (title/domain/description/visibility).
- **Literature Discovery**: search across the backend's 5 external sources,
  add a result to the workspace, upload a PDF directly, browse the paper list.
- **Activity log**: chronological feed of what happened in a workspace.

Mentors and Feed are visible in the sidebar but disabled ("SOON") — those
are Modules 8 and 11, not built on the backend yet, so there's nothing for
them to call.

## Design

- **Colors**: paper `#F7F6F3` background, ink `#1A1D23` text, navy `#1F3864`
  (sidebar/brand — carried over from the project's SRS/SDD/DDD documents),
  ochre `#B8752F` (primary actions).
- **Type**: a serif stack for headings (workspace titles, page headings),
  system sans-serif for UI text. Both are system-font stacks rather than
  Google Fonts — this sandbox's network couldn't reach fonts.googleapis.com,
  and system stacks also mean zero external font-loading dependency in any
  environment, so it was kept that way rather than reverting once deployed.
- **Layout**: a persistent left sidebar app-shell, not a marketing-style
  page — this is a tool people return to.

## Setup

```bash
npm install
cp .env.local.example .env.local   # points at http://localhost:8000/api/v1 by default
npm run dev
```

Open `http://localhost:3000`. You'll need the backend running too (see
`researchos-backend/README.md`) — CORS is already configured on the backend
for `http://localhost:3000`.

## Known trade-offs / not done

- **Tokens are stored in localStorage**, not an httpOnly cookie. Simplest
  thing that works for local development; a production hardening pass
  should move refresh-token issuance behind a Next.js route handler that
  sets an httpOnly cookie instead (noted in `lib/token-store.ts`).
- **No pagination UI** — the workspace and paper lists call the backend's
  paginated endpoints but always request page 1; there's no "load more" or
  page control yet, since nobody has more than 20 of anything yet in this
  build's usage.
- **No toasts/optimistic updates** — actions (create workspace, add paper)
  wait for the server response before updating the UI. Simple and correct,
  just not the snappiest possible feel.
- **No tests** — this build pass prioritized getting the three modules
  working end-to-end against the real backend over frontend test coverage.
  A reasonable next step would be Playwright tests for the three main flows
  (register→login, create workspace, search→add paper).

## Project layout

```
app/
  layout.tsx              Root layout (fonts via CSS variables, AuthProvider)
  page.tsx                 Redirects to /login or /workspaces based on auth
  login/page.tsx
  register/page.tsx
  (app)/layout.tsx          Sidebar app-shell + auth guard for everything inside
  (app)/workspaces/page.tsx           List + create
  (app)/workspaces/[id]/page.tsx      Detail: header, tabs, edit
  (app)/workspaces/[id]/papers-tab.tsx     Literature search + paper list + upload
  (app)/workspaces/[id]/activity-tab.tsx   Activity log

lib/
  api.ts                Typed client for every Module 1-3 endpoint, with auto token refresh
  auth-context.tsx        React context wrapping api.ts with user state
  token-store.ts           localStorage read/write for access/refresh tokens

components/
  ui.tsx                  Button, Input, Card, Badge, EmptyState, etc.
```
