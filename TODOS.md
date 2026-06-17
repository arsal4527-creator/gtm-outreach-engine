# TODOS

Deferred work, with enough context to pick up cold.

## P2 — Content loop: auto-draft build-in-public LinkedIn posts

- **What:** Add an n8n node that turns each morning's run into a short drafted LinkedIn
  post (e.g. "today's run found N companies hiring GTM engineers; the most common GTM
  gap was X"). Draft only — you review and publish.
- **Why:** Outreach today is purely outbound. A content loop compounds inbound interest
  from recruiters and founders, which matters disproportionately for a remote candidate
  fighting a geography discount. The engine already has the raw material each run.
- **Pros:** Builds a public track record; pulls inbound; reuses data the pipeline
  already produces.
- **Cons:** A second surface to maintain; borders on a different strategy (Direction C);
  risk of low-quality posts if not reviewed.
- **Context:** Decided in the 2026-06-16 CEO review (SELECTIVE EXPANSION). Deferred so
  Direction B's core (honest docs, proof-in-email, public dashboard) ships first. Build
  point: a Code/LLM node after the run summary, writing to a "drafts" surface (a Sheet
  tab or a Gmail draft to self), never auto-posting.
- **Effort:** M (human ~half day) → with CC: S (~45 min).
- **Priority:** P2.
- **Depends on:** Direction B core shipped and validated first.
