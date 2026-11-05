# PostHog Design System — Opportunity Hunter AI Implementation

## Overview

PostHog's marketing system is built on the visual contradiction at the heart of the brand: a serious open-source product analytics platform rendered as if it were a friendly engineering sketchbook. The chrome runs on a warm cream canvas (`{colors.canvas}` — `#eeefe9`) — not white — and every page is dotted with hand-drawn hedgehog mascots in lab coats, lounge chairs, terminals, and reading glasses, scattered across the layout like marginalia in a textbook. Type sits in IBM Plex Sans Variable at olive-gray (`{colors.body}` — `#4d4f46`) for body and deep olive-charcoal (`{colors.ink}` — `#23251d`) for headlines, with weights stepped tightly between 400, 600, 700, and 800 to create hierarchy without color. The single saturated yellow-orange pill (`{colors.primary}` — `#f7a501`) is the brand's only loud chromatic moment; everything else is cream, olive, white card, and the occasional pastel callout band.

The system has a distinctive **two-mode body layout**: marketing pages lean on alternating-pastel callout bands and feature tiles in white cards on cream, while documentation pages add a sticky 240px left sidebar with a rounded outline-icon section list. Code samples are full-width dark blocks on `{colors.surface-dark}` (the same olive-charcoal that carries body ink, used inverted) inside white doc cards, creating the system's most distinctive visual moment: a dark-on-dark code island floating inside a white card on a cream canvas, with a hedgehog mascot doodled in the margin.

Sections stack at `{spacing.section}` (80px) rhythm with cream canvas continuing edge-to-edge between them. The only color bands that interrupt the cream are pastel `{component.banner-tip-blue}` / `-green` / `-red` / `-purple` callout panels inside doc articles — soft tinted boxes that carry "💡 Tip", "✅ Success", "⚠️ Warning", "📘 Info" inline annotations. There are no decorative gradients, no atmospheric mesh backgrounds, and no full-bleed dark hero chapters; the cream canvas runs uninterrupted top to bottom and the hedgehogs are the entire visual identity.

**Key Characteristics:**
- Warm cream canvas (`{colors.canvas}` — #eeefe9) end-to-end with no surface alternation between sections — the page is one continuous sheet
- Single yellow-orange CTA pill (`{colors.primary}` — #f7a501) with deep olive text (`{colors.on-primary}`) — the brand's only saturated color
- IBM Plex Sans Variable across every text role with weights 400/500/600/700/800 — no other typeface in the system
- Hand-drawn hedgehog mascots scattered across the layout as the entire decorative system — no gradients, no mesh, no atmospheric backgrounds
- 4–8px radius card vocabulary: `{rounded.md}` (6px) for most components, `{rounded.lg}` (8px) for select containers, fully rounded for pill chips
- Pastel callout banners (`{colors.accent-blue-soft}`, `{colors.accent-green-soft}`, `{colors.accent-red-soft}`, `{colors.accent-purple-soft}`) break up doc article body with soft tinted side rails for tips/warnings/info
- Documentation pages add a sticky 240px `{component.doc-sidebar}` with rounded outline-icon section nav and an "Ask PostHog AI" CTA at the top

## Colors

### Brand & Accent
- **PostHog Yellow** (`{colors.primary}` — `#f7a501`): the universal primary CTA. Sticky "Get started — free" pill in the top-right of every nav, hero CTAs, pricing-tier subscribe buttons, footer signup pill. The system's only saturated chromatic moment.
- **Yellow Pressed** (`{colors.primary-pressed}` — `#dd9001`): pressed state for the primary pill.
- **Yellow Active** (`{colors.primary-active}` — `#b17816`): deeply-pressed yellow + the system's gold-toned border accent (rare 1px gold rule on inline form elements).

### Surface
- **Canvas** (`{colors.canvas}` — `#eeefe9`): the warm cream page background. End-to-end on every page; the brand's most distinctive surface choice.
- **Soft Surface** (`{colors.surface-soft}` — `#e5e7e0`): button-secondary fill, sub-nav strip background, inline-code chip background.
- **Surface Card** (`{colors.surface-card}` — `#ffffff`): true white card and tile background sitting on top of the cream canvas. The dominant card surface.
- **Surface Doc** (`{colors.surface-doc}` — `#fcfcfa`): a faintly cream-warm white used inside doc article body cards — slightly softer than pure white to keep the page tonally unified.
- **Surface Dark** (`{colors.surface-dark}` — `#23251d`): the deep olive-charcoal used inverted as code-block background. The same hex as `{colors.ink}` — the brand uses one olive-near-black for both text and dark code surfaces.
- **Hairline** (`{colors.hairline}` — `#bfc1b7`): 1px card border, table rule, footer column dividers.
- **Hairline Soft** (`{colors.hairline-soft}` — `#dcdfd2`): in-card row divider, soft inset rule.
- **On Dark** (`{colors.on-dark}` — `#ffffff`): primary text on `{colors.surface-dark}` code blocks.

### Text
- **Ink** (`{colors.ink}` — `#23251d`): headlines, button text on light, primary nav links — deep olive-charcoal that reads near-black against cream.
- **Body** (`{colors.body}` — `#4d4f46`): default paragraph text, doc article body, inline link color before hover. The brand's most-used text color.
- **Charcoal** (`{colors.charcoal}` — `#33342d`): emphasized body text where body is too soft.
- **Mute** (`{colors.mute}` — `#6c6e63`): metadata, footer link text, in-list secondary annotations.
- **Ash** (`{colors.ash}` — `#9b9c92`): disabled-state text and lowest-emphasis utility.
- **Stone** (`{colors.stone}` — `#b6b7af`): least-emphasis caption text and disabled icon color.

### Semantic
- **Link Blue** (`{colors.link-blue}` — `#1d4ed8`): inline anchor link inside body prose. The system's primary informational link color.
- **Link Teal** (`{colors.link-teal}` — `#1078a3`): doc-article inline link variant, paired with body text.
- **Accent Blue** (`{colors.accent-blue}` — `#2c84e0`) + **Accent Blue Soft** (`{colors.accent-blue-soft}` — `#dceaf6`): "💡 Tip / Info" callout banner inside docs.
- **Accent Red** (`{colors.accent-red}` — `#cd4239`) + **Accent Red Soft** (`{colors.accent-red-soft}` — `#f7d6d3`): "⚠️ Warning / Caution" callout banner.
- **Accent Green** (`{colors.accent-green}` — `#2c8c66`) + **Accent Green Soft** (`{colors.accent-green-soft}` — `#d9eddf`): "✅ Success / Positive" callout banner.
- **Accent Purple** (`{colors.accent-purple}` — `#7c44a6`) + **Accent Purple Soft** (`{colors.accent-purple-soft}` — `#e7d8ee`): "📘 Note / Reference" callout banner.
- **Focus Ring** (`{colors.focus-ring}` — `rgba(59,130,246,0.5)`): translucent blue browser-default focus ring around interactive elements.

## Typography

### Font Family
**IBM Plex Sans Variable** is the system's primary face — used across every text role on every page at weights 400 (regular), 500 (medium), 600 (semibold), 700 (bold), and 800 (extra-bold). Falls back through `IBM Plex Sans` → `-apple-system` → `system-ui` → broad cross-platform sans stack.

**ui-monospace** + **Source Code Pro** / **JetBrains Mono** carry code samples and inline-code chips at 14px / 1.43 line-height.

The brand-distinctive choice is the **mixed weight ladder** (400 / 500 / 600 / 700 / 800) — most chrome lives in the 400–700 band, with weight 800 reserved exclusively for the larger display headlines on home and pricing. This gives the system its "engineering blog" feel: hierarchy is built from weight contrast much more than from size.

## Elevation & Shapes

- **Flat elevation:** No drop shadows. Cards sit flat on cream with 1px solid `{colors.hairline}` borders (`#bfc1b7`).
- **Border radius:** `{rounded.md}` (6px) for cards, doc cards, buttons, code blocks; `{rounded.full}` for pills; `{rounded.xs}` (2px) for inline code chips.
