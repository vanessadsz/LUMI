---
name: Editorial Parchment
colors:
  surface: '#F0E0C9'
  surface-dim: '#E4CDAE'
  surface-bright: '#F8EEDF'
  surface-container-lowest: '#F8EEDF'
  surface-container-low: '#F0E0C9'
  surface-container: '#DFC6A5'
  surface-container-high: '#DFC6A5'
  surface-container-highest: '#D9BE9A'
  on-surface: '#590907'
  on-surface-variant: '#A5A79B'
  inverse-surface: '#590907'
  inverse-on-surface: '#E8D2B5'
  outline: 'rgba(89,9,7,0.16)'
  outline-variant: 'rgba(89,9,7,0.10)'
  surface-tint: '#590907'
  primary: '#590907'
  on-primary: '#E8D2B5'
  primary-container: '#590907'
  on-primary-container: '#E8D2B5'
  inverse-primary: '#E8D2B5'
  secondary: '#A5A79B'
  on-secondary: '#590907'
  secondary-container: '#A5A79B'
  on-secondary-container: '#590907'
  tertiary: '#3A0504'
  on-tertiary: '#E8D2B5'
  tertiary-container: '#D9BE9A'
  on-tertiary-container: '#3A0504'
  error: '#B3261E'
  on-error: '#E8D2B5'
  error-container: 'rgba(179,38,30,0.10)'
  on-error-container: '#B3261E'
  primary-fixed: '#DFC6A5'
  primary-fixed-dim: '#D9BE9A'
  on-primary-fixed: '#590907'
  on-primary-fixed-variant: '#3A0504'
  secondary-fixed: '#DFC6A5'
  secondary-fixed-dim: '#D9BE9A'
  on-secondary-fixed: '#590907'
  on-secondary-fixed-variant: '#3A0504'
  tertiary-fixed: '#DFC6A5'
  tertiary-fixed-dim: '#D9BE9A'
  on-tertiary-fixed: '#3A0504'
  on-tertiary-fixed-variant: '#590907'
  background: '#E8D2B5'
  on-background: '#590907'
  surface-variant: '#DFC6A5'
  canvas: '#E8D2B5'
  panel: '#DFC6A5'
  border-subtle: 'rgba(89,9,7,0.10)'
  border-default: 'rgba(89,9,7,0.16)'
  border-strong: 'rgba(89,9,7,0.26)'
  text-emphasis: '#3A0504'
  text-primary: '#590907'
  text-secondary: '#A5A79B'
  text-disabled: 'rgba(89,9,7,0.40)'
  accent-hover: '#6A0F0C'
  accent-pressed: '#490605'
  accent-tint: 'rgba(89,9,7,0.10)'
  success: '#4F6B3A'
  warning: '#9A6A12'
  danger: '#B3261E'
  info: '#3F6178'
  footer-bg: '#A5A79B'
  footer-text: '#590907'
typography:
  display-xl:
    fontFamily: Inter Variable, Inter, sans-serif
    fontSize: 72px
    fontWeight: '510'
    lineHeight: 72px
    letterSpacing: -0.022em
  display-l:
    fontFamily: Inter Variable, Inter, sans-serif
    fontSize: 64px
    fontWeight: '510'
    lineHeight: 67px
    letterSpacing: -0.022em
  heading-1:
    fontFamily: Inter Variable, Inter, sans-serif
    fontSize: 48px
    fontWeight: '510'
    lineHeight: 52px
    letterSpacing: -0.02em
  heading-2:
    fontFamily: Inter Variable, Inter, sans-serif
    fontSize: 32px
    fontWeight: '510'
    lineHeight: 38px
    letterSpacing: -0.016em
  heading-3:
    fontFamily: Inter Variable, Inter, sans-serif
    fontSize: 24px
    fontWeight: '510'
    lineHeight: 30px
    letterSpacing: -0.012em
  heading-4:
    fontFamily: Inter Variable, Inter, sans-serif
    fontSize: 20px
    fontWeight: '590'
    lineHeight: 26px
    letterSpacing: -0.01em
  body-l:
    fontFamily: Inter Variable, Inter, sans-serif
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 27px
    letterSpacing: 0
  body-md:
    fontFamily: Inter Variable, Inter, sans-serif
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: 0
  body-sm:
    fontFamily: Inter Variable, Inter, sans-serif
    fontSize: 13px
    fontWeight: '510'
    lineHeight: 20px
    letterSpacing: 0
  label-sm:
    fontFamily: Inter Variable, Inter, sans-serif
    fontSize: 12px
    fontWeight: '510'
    lineHeight: 16px
    letterSpacing: 0
  micro-label:
    fontFamily: Inter Variable, Inter, sans-serif
    fontSize: 11px
    fontWeight: '510'
    lineHeight: 14px
    letterSpacing: 0.04em
  mono-default:
    fontFamily: Berkeley Mono, ui-monospace, SF Mono, Menlo, monospace
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0
rounded:
  sm: 4px
  DEFAULT: 6px
  md: 6px
  lg: 8px
  xl: 12px
  full: 999px
spacing:
  base: 4px
  space-1: 4px
  space-2: 8px
  space-3: 12px
  space-4: 16px
  space-5: 20px
  space-6: 24px
  space-8: 32px
  space-10: 40px
  space-12: 48px
  space-16: 64px
  space-24: 96px
  space-32: 128px
---

# Editorial Parchment — Warm Light-Mode-First Design System

## 1. Aesthetic Mood & North Star
Precise, quiet, high-density, engineered, warm and editorial.
- Canvas parchment base: Warm Cream Beige (#E8D2B5)
- Deep Burgundy ink (#590907) for typography, primary accents, hairline borders
- Muted Sage Grey (#A5A79B) as calm secondary voice and footer
- Zero pure black (#000000), zero pure white (#FFFFFF), zero cool grays.
- Depth comes from surface lightness steps and 1px borders, never heavy black shadows.

## 2. Palette Architecture
- Base Canvas: #E8D2B5
- Panel (Sidebars, secondary panes): #DFC6A5
- Surface (Cards, rows, inputs): #F0E0C9
- Surface Elevated (Popovers, menus, modals): #F8EEDF
- Surface Hover: #E4CDAE
- Surface Active / Selected: #D9BE9A
- Hairline Borders: subtle rgba(89,9,7,0.10), default rgba(89,9,7,0.16), strong rgba(89,9,7,0.26)
- Text Emphasis: #3A0504
- Text Primary: #590907
- Text Secondary: #A5A79B (set at 510 weight minimum, 13px minimum on cream)
- Text Disabled / Placeholder: rgba(89,9,7,0.40)
- Accents: #590907 (hover #6A0F0C, pressed #490605, text #E8D2B5)
- Semantic: Success #4F6B3A, Warning #9A6A12, Danger #B3261E, Info #3F6178

## 3. Elevation & Shadow Spec
Shadows are burgundy-tinted, never black:
- Level 0: no shadow, 1px border default.
- Level 1: border default plus `0 8px 24px rgba(89,9,7,0.16)`
- Level 2: border strong plus `0 24px 64px rgba(89,9,7,0.28)`, backdrop rgba(89,9,7,0.45) with 4px blur.

## 4. Components
- Buttons: 6px radius, 13px/510, transition 120ms. Primary (#590907 text #E8D2B5), Secondary (#F0E0C9 text #590907), Ghost, Danger.
- Inputs: 32px height, #F0E0C9 fill, border default, 6px radius, focus border #590907 with 3px ring rgba(89,9,7,0.18).
- Checkboxes: 16px, radius 4px, #590907 check on cream.
- Badges: 20px height, radius 999px, 12px/510, 14% fill with 24% border.

