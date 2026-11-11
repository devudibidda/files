# TrendWise DESIGN.md — Anthropic warm editorial system

Style guide for the TrendWise frontend. Source: Refero Styles, Claude design
system (https://styles.refero.design/style/47cb86b6-cb2d-41c8-94ba-8607cd7c41cd),
with the Anthropic variant's ivory canvas and 68px display scale. Applied
2026-11-09, replacing the old dark glass theme.

## Rule

Match this file exactly. Do not invent new colors, fonts, radii, or shadows.
When a new component is needed, reuse the tokens and patterns below.

## Tokens — Colors

| Name | Value | Role |
|---|---|---|
| Bone Parchment | `#f8f8f6` | Page canvas, never pure white for large backgrounds |
| Paper White | `#ffffff` | Card surfaces |
| Ivory Medium | `#f0eee6` | Secondary surfaces |
| Manilla | `#f5e3c7` | Warm highlight strip |
| Carbon Ink | `#121212` | Primary text, filled actions. Never pure black `#000000` |
| Slate Dark | `#141413` | Headings |
| Graphite | `#3d3d3a` | Secondary text |
| Ash | `#87867f` | Muted text, labels |
| Pebble | `#b0aea5` | More muted text |
| Stone | `#cccbc8` | Borders, hairlines |
| Sand | `#e3dacc` | Hairline borders, fills |
| Clay | `#d97757` | The one chromatic accent, decorative marks and editorial accents only |
| Clay Deep | `#c6613f` | Clay hover |
| Success | `#02a745` | Semantic green (gains, buys) |
| Error | `#a10214` | Semantic red (losses, sells) |

## Tokens — Typography

- Display: Anthropic Serif, weight 400, sizes 24px and 30px for section
  titles, up to 56-68px for the hero headline, line-height 1.08-1.2.
  Web fallback: Source Serif 4, Charter, Georgia.
- UI: Anthropic Sans, weights 400-580, sizes 11-24px, line-height 1.33-1.63.
  Web fallback: Inter, IBM Plex Sans, system-ui. Weight 580 is the heaviest;
  never use 600+ for headlines, and never bold the serif.

## Tokens — Spacing & Shapes

- 64-80px between major sections, 32px card padding (24px on mobile),
  8-12px between elements inside a component.
- Radii: 24px elevated cards, 16px nested cards, 8px buttons and inputs.
  The glass sidebar keeps its 28px radius (pre-existing, harmonizes).
- Flat surfaces, minimal shadow, hairline borders. No gradients, no aurora,
  no glassmorphism on content cards.

## Guidelines

Do:
- Use Bone Parchment as the default page canvas.
- Set display headlines in the serif at weight 400 and let the serif do the work.
- Keep the palette monochrome; Clay is the only chromatic color.
- Pair Carbon Ink text with Paper White cards on Bone Parchment.
- Actions stay dark on light (ink button, parchment text). Clay never fills a button.

Don't:
- Don't introduce a second chromatic color for emphasis.
- Don't use pure black for body text.
- Don't use drop shadows, blurs, or gradient fills on cards or buttons.

## Motion (DesignSpells recipes)

- Animated numbers on KPI/index values: tween from the previous value over
  ~600ms, cubic ease-out, tabular numerals. Honors reduced-motion.
- Card hover: lift 4px, soft shadow fades in over 150ms.
- 3D tilt on dashboard cards (index strip, strong buys, movers, breadth):
  cards follow the cursor by at most 4 degrees with a 4px translateZ and
  the card's own soft shadow. No glare, no deep shadow, no tilt on the news
  card or hero text. Honors reduced-motion.
- Page reveal: fade + 12px rise over 0.6s, staggered 70ms per item, no blur.
- Sidebar: 500ms width transition with staggered label fade-in (kept).

## Hero pattern (Supahero)

One headline, one supporting line, one primary action, one strong visual.
On the dashboard the visual is the live index strip, with serif numerals.

## Implementation note

The Tailwind config maps the old dark-theme class names onto these tokens
(ink scale now holds warm light surfaces, slate holds warm ink text), so the
170+ existing usages flip with the tokens. See tailwind.config.js. New code
should use the semantic names (paper, ivory, clay, slate-100) directly.
