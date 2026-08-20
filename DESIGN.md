# SENTINEL-CHAIN: Master Design System, Brand Kit & UI/UX Specifications
Product: "SENTINEL-CHAIN" (Autonomous Cyber Threat Harvester & Self-Healing Scraper Engine)
Role Context: Principal Product Designer & Design Systems Architect

---

## SECTION 1: BRAND IDENTITY & DESIGN SYSTEM TOKENS

### 1.1 Brand Moodboard & Aesthetic Definition
- **Aesthetic Archetype:** Sleek Modern Enterprise SecOps Precision (Dark Mode Only).
- **Inspiration:** Atmospheric, hyper-refined dark aesthetic of Stripe and Linear (Atio/Airtable style).
- **Core Principles:** Deep neutral canvases (`#09090B`), razor-thin borders (`#27272A` / 40%), strict 8px/4px spacing, and color reserved almost exclusively for real-time semantic statuses.
- **The Psychological Halo Effect:** Within 50ms, judges and engineers perceive an expensive, production-ready enterprise security platform.

### 1.2 Exact Color Palette (Hex Codes & Rationale)
- **Canvas (`#09090B`):** Deep obsidian black background. Minimizes eye strain for SecOps during prolonged monitoring.
- **Surface (`#121215`):** Secondary base for sidebar navigation and nested layout panels.
- **Card / Panel (`#18181B`):** Standard widget cards and container surfaces (elevated 1 layer).
- **Overlay (`#202024`):** Dialog modals, tooltips, and floating context dropdown menus.
- **Border (Muted) (`#27272A` / 40%):** Ultra-thin 1px borders dividing content with soft contrast.
- **Border (Active) (`#3F3F46`):** Focused text inputs and highlighted states.
- **Primary Accent (`#6366F1`):** Cobalt Indigo. Used exclusively for critical CTAs, active nav items, and positive telemetry pathways.
- **Semantic Critical (`#EF4444`):** Vibrant Red. Signals broken scraper, pipeline failure, or injected sabotage.
- **Semantic Warning (`#F59E0B`):** Amber. Rate-limiting, pipeline degradation, or pending verification.
- **Semantic Healed (`#10B981`):** Emerald Green. Active node healing, successful bypass routing, clean data harvest.
- **Semantic Idle (`#71717A`):** Zinc Slate. Dormant, inactive, or offline monitoring channels.

### 1.3 Typography Scale & Baseline Rhythm
- **Primary Display / UI Font:** Geist Sans / Inter (`text-5xl font-bold`, `text-4xl font-bold`, `text-2xl font-semibold`, `text-sm font-normal`).
- **Monospace Font:** JetBrains Mono / Geist Mono (`font-mono text-xs font-medium`).
- **Baseline Rhythm:** All line-height values mathematically locked to multiples of 4px.

### 1.4 Spacing & Elevation System
- **Spacing Scale:** `$spacing-xs` (4px), `$spacing-sm` (8px), `$spacing-md` (16px), `$spacing-lg` (24px), `$spacing-xl` (32px), `$spacing-2xl` (48px).
- **Border Radii:** `radius-lg` (12px - Cards/Panels), `radius-md` (8px - Inputs/Buttons), `radius-sm` (4px - Tags/Badges).
- **Shadows:** Standard Card `shadow-[0_8px_30px_rgb(0,0,0,0.4)]`, Indigo Glow `shadow-[0_0_25px_rgba(99,102,241,0.15)]`, Emerald Pulse `shadow-[0_0_30px_rgba(16,185,129,0.25)]`.

---

## SECTION 2: END-TO-END USER JOURNEY & INFORMATION ARCHITECTURE
- **Persona 1: Hackathon Judge (120-Second "Aha!" Moment):** Fast cognitive fluency. Primary CTA `[Inject Scraper Sabotage Block]` triggers instant visual failure, auto-healing DAG reroute, code diff Green flash, and confetti burst in under 5 seconds.
- **Persona 2: Enterprise SecOps Engineer (Trust through Transparency):** Deep inspection via Split-Screen Diff Inspector, side-by-side YAML/Python selectors, Playwright AOM proof, and SQLite WAL persisted telemetry.

---

## SECTION 3: LANDING PAGE & HERO SECTION BLUEPRINT
- **12-Column Desktop Grid (`max-w-7xl mx-auto px-6`):**
  - **Hero Section:** Left 5-cols (Display H1, Live Terminal Prompt, CTAs, Trust Metrics) + Right 7-cols (Interactive Reactor DAG Telemetry Simulation).
  - **Section A:** Architecture Visualizer Bento Grid (3-step pipeline flow).
  - **Section B:** Live Sandbox Playground (Control Board + Monospaced Log Stream).
  - **Section C:** Enterprise Security Specs & Benchmarks Table.

---

## SECTION 4: CORE APP & DASHBOARD WIREFRAME
- **Split-Pane Workspace:**
  - Left Nav Sidebar (Col-span 2): Harvests, Pipelines, Proxies, Logs, Health.
  - Center Workspace (Col-span 7): Top React Flow DAG (60%) + Bottom Threat Live-Stream (40%).
  - Right Details Inspector (Col-span 3): Value Diff Inspector with Side-by-Side YAML/Code Diff and Real-Time SSE Log Stream.
