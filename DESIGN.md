# Design System: SENTINEL-CHAIN (Cyber Threat Intelligence Self-Healing Engine)

## 1. Visual Theme & Atmosphere
A restrained, high-density yet breathable security operations dashboard with surgical precision and subtle spring-physics feedback. The aesthetic is deep obsidian charcoal with whisper hairline borders and a singular emerald/teal accent reserved strictly for active states, healthy nodes, and verified recovery events.

- **Density:** Cockpit Dense (8/10) with progressive disclosure
- **Variance:** Offset Asymmetric 3-Column Cockpit (6/10)
- **Motion:** Fluid CSS & Spring Micro-Interactions (6/10)

---

## 2. Color Palette & Roles
- **Deep Void Canvas** (`#080B11`) — Main background canvas surface
- **Elevated Bento Surface** (`#0F131C`) — Card panels and containers (12px radius)
- **Interactive Container** (`#151B27`) — Hover states, input fields, selected mode cards
- **Hairline Border** (`rgba(255, 255, 255, 0.07)`) — Structural 1px division lines
- **Active Border Accent** (`rgba(16, 185, 129, 0.40)`) — Focus and active pipeline paths
- **Singular Brand Accent (Emerald)** (`#10B981`) — Verified healthy, active CTAs, approved state
- **Telemetry Accent (Cyan)** (`#0EA5E9`) — SSE connection pulse, CLI commands, active streams
- **Alert Amber** (`#F59E0B`) — Mutation detected, warning telemetry
- **Failure Crimson** (`#EF4444`) — Scraper broken, malicious payload blocked
- **Primary Text** (`#F8FAFC`) — High contrast headlines, CVE IDs, critical values
- **Secondary Muted** (`#94A3B8`) — Descriptions, column labels
- **Muted Steel** (`#64748B`) — Timestamps, metadata, technical labels

---

## 3. Typography Rules
- **Display / UI Sans:** Modern sans-serif stack (`-apple-system`, `BlinkMacSystemFont`, `Segoe UI`, `Roboto`, `sans-serif`)
- **Technical Monospace:** Monospace stack for all CVE IDs, timestamps, latency metrics, selector strings, and terminal logs (`ui-monospace`, `SFMono-Regular`, `Menlo`, `Monaco`, `Consolas`, monospace)
- **Anti-Patterns Banned:** No emojis, no serif fonts in UI controls, no rainbow gradients.

---

## 4. Component Stylings (Anti-Slop Directives)
- **Cards & Bento Panels:** Exactly `12px` corner radius (`rounded-[12px]`). 1px hairline border `rgba(255, 255, 255, 0.07)`. Diffused whisper shadow `box-shadow: 0 10px 30px rgba(0,0,0,0.03)`. Card padding minimum `24px` (`p-6`) for primary sections.
- **Buttons:** Tactile feedback on active (`active:scale-[0.98]`). Primary action uses emerald/teal solid accent with dark contrast text. Secondary action uses subtle neutral fill with hairline border.
- **Badges & Chips:** Exactly `6px` corner radius. Subtle translucent backgrounds (`bg-emerald-950/40`, `border-emerald-800/60`).
- **Loaders & Skeletons:** Soft gray/zinc skeleton shimmer bars instead of generic spinning wheels.
- **Data Safety:** Text ellipsis (`truncate`), `line-clamp-2` for variable CVE vulnerability titles.

---

## 5. Motion & Micro-Interactions
- **Transitions:** 150ms–200ms ease-out transitions for hover and active state changes.
- **DAG Flow Animations:** Real-time animated edges with SVG markers. Active nodes exhibit a subtle breathing pulse.
- **Live Stream Transitions:** New threat entries animate into the live feed smoothly.
