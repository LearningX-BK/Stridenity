---
name: stridenity-ui
description: ANUPAL frontend design system and UI rules — Stridenity brand tokens, light/dark themes, layout, components, AI marking, status chips, Indian formats, accessibility, mobile/PWA. Use for every frontend task.
---

# Stridenity UI

Source of truth: `docs/UX.md` (tokens §1, IA §2, screens §3, interaction rules §4). The clickable
concept is `prototype/index.html` — match its information design and tone, not its code.

## Rules
- Colours, radii, spacing, shadows only via CSS variables from `src/styles/tokens.css`
  (Tailwind theme maps to them). No hex in components. Gradient (`--brand-gradient`) only for the
  logo mark, product mark and at most one hero accent per screen.
- Status chips: `<StatusChip status="overdue" />` — text + icon + colour; statuses: scheduled,
  open, in_preparation, in_review, pending_approval, approved, filed, closed, overdue, na,
  applied_awaiting_grant. Risk badges H/M/L.
- AI content: violet left rule + `<AIChip />` + "Why?" (WhyDrawer) until a human approves.
- Every list has empty, loading (skeleton) and error states; every empty state says what to do next.
- Tables: sticky header, column chooser, density toggle; below 768 px render cards.
- Numbers: `formatINR(paise)` → ₹1,23,456; dates `15 Oct 2026`; times IST; tabular numerals.
- Forms: label + help text ("Why we ask"); validation inline in plain language; never block on
  optional fields.
- Accessibility: WCAG 2.1 AA, focus visible (`--focus`), keyboard paths for approve/return,
  44 px touch targets, `prefers-reduced-motion` respected.
- i18n: all strings via `t()`; site-user/contractor screens and generated notices in EN/HI/MR.
- Both themes and 390 px mobile are checked for every new screen with `scripts/ui_check.py`.
- Base path aware routing; no absolute `/assets` URLs.
- Event handlers: no inline closures that build strings for ids in lists — pass ids via
  `data-*` attributes or typed props (lesson from the HMS prototype).
