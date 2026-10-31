---
name: Editorial Parchment — Warm Light-Mode-First Design System
version: 1.0.0
palette:
  warm-cream-beige: '#E8D2B5' # Base canvas
  deep-burgundy: '#590907'    # Primary text, primary actions, hairline borders
  muted-sage-grey: '#A5A79B'  # Secondary text, footer ground, neutral badges
tokens:
  light:
    canvas: '#E8D2B5'
    panel: '#DFC6A5'
    surface: '#F0E0C9'
    surface-elevated: '#F8EEDF'
    surface-hover: '#E4CDAE'
    surface-active: '#D9BE9A'
    border-subtle: 'rgba(89, 9, 7, 0.10)'
    border-default: 'rgba(89, 9, 7, 0.16)'
    border-strong: 'rgba(89, 9, 7, 0.26)'
    text-emphasis: '#3A0504'
    text-primary: '#590907'
    text-secondary: '#A5A79B'
    text-disabled: 'rgba(89, 9, 7, 0.40)'
    accent: '#590907'
    accent-hover: '#6A0F0C'
    accent-pressed: '#490605'
    accent-text: '#E8D2B5'
    accent-tint: 'rgba(89, 9, 7, 0.10)'
    secondary-neutral: '#A5A79B'
    success: '#4F6B3A'
    warning: '#9A6A12'
    danger: '#B3261E'
    info: '#3F6178'
    hero-glow: 'radial-gradient(ellipse 60% 40% at 50% 0%, rgba(248,238,223,0.85) 0%, rgba(232,210,181,0) 70%)'
    headline-gradient: 'linear-gradient(180deg, #3A0504 0%, #590907 100%)'
  dark:
    canvas: '#590907'
    panel: '#490605'
    surface: '#6A0F0C'
    surface-elevated: '#7A1815'
    surface-hover: '#84201C'
    border-default: 'rgba(232, 210, 181, 0.16)'
    text-emphasis: '#F6EBDC'
    text-primary: '#E8D2B5'
    text-secondary: '#A5A79B'
    text-disabled: '#8A8478'
    accent: '#E8D2B5'
    accent-text: '#590907'
    accent-hover: '#F1DFC6'
    accent-pressed: '#D4BC9B'
typography:
  family:
    sans: '"Inter Variable", "Inter", -apple-system, "SF Pro Text", "Segoe UI", sans-serif'
    mono: '"Berkeley Mono", ui-monospace, "SF Mono", Menlo, monospace'
    features: '"cv01" 1, "ss03" 1'
  scale:
    display-xl: { size: 72px, line-height: 72px, weight: 510, tracking: -0.022em }
    display-l: { size: 64px, line-height: 67px, weight: 510, tracking: -0.022em }
    heading-1: { size: 48px, line-height: 52px, weight: 510, tracking: -0.020em }
    heading-2: { size: 32px, line-height: 38px, weight: 510, tracking: -0.016em }
    heading-3: { size: 24px, line-height: 30px, weight: 510, tracking: -0.012em }
    heading-4: { size: 20px, line-height: 26px, weight: 590, tracking: -0.010em }
    body-l: { size: 18px, line-height: 27px, weight: 400, tracking: 0 }
    body: { size: 15px, line-height: 24px, weight: 400, tracking: 0 }
    ui: { size: 13px, line-height: 20px, weight: 510, tracking: 0 }
    small: { size: 12px, line-height: 16px, weight: 510, tracking: 0 }
    micro-label: { size: 11px, line-height: 14px, weight: 510, tracking: 0.04em, text-transform: uppercase }
    mono: { size: 12px, line-height: 18px, weight: 400, tracking: 0 }
radii:
  sm: 4px      # tags, checkboxes
  default: 6px # buttons, inputs, menu items
  md: 8px      # cards, popovers
  lg: 12px     # large panels, modals, command palette
  full: 999px  # avatars, pills
elevation:
  level-0: '1px solid rgba(89, 9, 7, 0.16)'
  level-1: '1px solid rgba(89, 9, 7, 0.16), 0 8px 24px rgba(89, 9, 7, 0.16)'
  level-2: '1px solid rgba(89, 9, 7, 0.26), 0 24px 64px rgba(89, 9, 7, 0.28)'
motion:
  easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)'
  durations:
    hover: 120ms
    press: 80ms
    menus: 160ms
    panels: 240ms
    page-fade: 320ms
---

# Editorial Parchment: Master Design System Specification

## 1. Aesthetic Mood & Creative North Star
Precise, quiet, high-density, engineered, warm and editorial.
The canvas is cream parchment (`#E8D2B5`), ink is deep burgundy (`#590907`), and hairline burgundy borders provide structural demarcation. Muted Sage Grey (`#A5A79B`) provides a calm secondary voice.
Zero pure black (`#000000`), zero pure white (`#FFFFFF`), and zero cool grays appear anywhere. All depth emerges through surface lightness steps and 1px borders, never heavy black drop shadows.

## 2. Global Palette Architecture
### Core Brand Tokens
- **Warm Cream Beige**: `#E8D2B5`
- **Deep Burgundy**: `#590907`
- **Muted Sage Grey**: `#A5A79B`

### Light Theme (Primary)
- **Canvas / App Background**: `#E8D2B5`
- **Panel (Sidebar, detail panes)**: `#DFC6A5`
- **Surface (Cards, rows, inputs)**: `#F0E0C9`
- **Surface Elevated (Popovers, menus, modals)**: `#F8EEDF`
- **Surface Hover**: `#E4CDAE`
- **Surface Active / Selected**: `#D9BE9A`
- **Border Subtle**: `rgba(89, 9, 7, 0.10)`
- **Border Default**: `rgba(89, 9, 7, 0.16)`
- **Border Strong**: `rgba(89, 9, 7, 0.26)`
- **Text Emphasis (Headlines)**: `#3A0504`
- **Text Primary**: `#590907`
- **Text Secondary**: `#A5A79B` (Weight ≥ 510, Size ≥ 13px)
- **Text Disabled / Placeholder**: `rgba(89, 9, 7, 0.40)`
- **Accent**: `#590907` (Hover: `#6A0F0C`, Pressed: `#490605`, Text: `#E8D2B5`)
- **Accent Tint**: `rgba(89, 9, 7, 0.10)`
- **Semantic Signals**: Success `#4F6B3A`, Warning `#9A6A12`, Danger `#B3261E`, Info `#3F6178`
- **Hero Glow**: `radial-gradient(ellipse 60% 40% at 50% 0%, rgba(248,238,223,0.85) 0%, rgba(232,210,181,0) 70%)`
- **Headline Gradient**: `linear-gradient(180deg, #3A0504 0%, #590907 100%)`

### Dark Theme (Secondary Toggle)
- **Canvas**: `#590907`, **Panel**: `#490605`, **Surface**: `#6A0F0C`, **Surface Elevated**: `#7A1815`
- **Text Emphasis**: `#F6EBDC`, **Text Primary**: `#E8D2B5`, **Text Secondary**: `#A5A79B`
- **Accent**: `#E8D2B5`, **Accent Text**: `#590907`

## 3. Reference Screens Built in Stitch
- **Project Name**: `Editorial Parchment - Warm Light Design System`
- **Project Resource**: `projects/642245963584748990`
- **Design System Asset**: `assets/acb837b7c5214963b7c55c2100d7f7b0`

1. **Page 1: Foundations (Design Tokens Page)**
   - Resource: `projects/642245963584748990/screens/49bb73882c2d4bce9f8d07591caaad77`
   - Three 200px hero swatch cards (Warm Cream Beige, Deep Burgundy, Muted Sage Grey).
   - 4-column derived swatch matrix, full typography specimen, spacing bars (4px–64px), radii, elevation cards, and motion demo chips.

2. **Page 2: Components Library**
   - Resource: `projects/642245963584748990/screens/29641f22b234442eaadff96612c2789a`
   - Sticky 200px anchor nav + 13 live component specimen cards on `#DFC6A5` dotted stages.
   - Matrix includes buttons, inputs, selects, toggles, badges, avatars, segmented tabs, popovers, tooltips, toasts, tables, modals, and command palette (`⌘K`).

3. **Page 3: App Shell Reference**
   - Resource: `projects/642245963584748990/screens/a8ef51c398084eeea096b4b61c0337aa`
   - 244px collapsible sidebar, 48px top bar with breadcrumbs and ghost view triggers, 36px grouped list rows with selected left accent bar, and 380px right detail inspector panel with audit trail.

4. **Page 4: Marketing Landing**
   - Resource: `projects/642245963584748990/screens/ed03479cafc240ce8e7171c1f26bcec4`
   - 56px sticky blurred nav, 128px padded hero with radial glow, 64px gradient headline, dual CTAs, live product frame preview, 3-column feature grid with Burgundy and Sage highlight cards, and full-bleed `#A5A79B` sage footer.

5. **Page 5: Settings & Workspace Configuration**
   - Resource: `projects/642245963584748990/screens/64261bd01ebe45ccbc8c431c61dacdc9`
   - Two-column configuration workbench: 220px navigation, 640px content area, identity and volume cadences, typesetting switches, and `#B3261E` Danger Zone card.

