# TrendWise DESIGN.md — Skeuomorphic material system

Style guide for the TrendWise frontend. Source: UI UX Pro Max skill,
skeuomorphism style entry (realistic textures, 8-12 stop gradients,
multi-layer shadows, tactile 300-500ms press). Applied 2026-11-15,
replacing the flat Anthropic system. Palette stays warm editorial
(parchment / ink / clay); the materials are new, the hues are not.

## Rule

Match this file exactly. Do not invent new colors, fonts, radii, or shadows.
When a new component is needed, reuse the materials and patterns below.
All materials are CSS-only (layered gradients + SVG grain data URI),
no image assets.

## Tokens — Colors

| Name | Value | Role |
|---|---|---|
| Bone Parchment | `#f8f8f6` | Page canvas, never pure white for large backgrounds |
| Paper White | `#ffffff` | Card faces |
| Ivory Medium | `#f0eee6` | Secondary surfaces |
| Manilla | `#f5e3c7` | Warm highlight strip, leather text |
| Carbon Ink | `#121212` | Primary text, filled actions. Never pure black `#000000` |
| Slate Dark | `#141413` | Headings |
| Graphite | `#3d3d3a` | Secondary text |
| Ash | `#87867f` | Muted text, labels |
| Pebble | `#b0aea5` | More muted text |
| Stone | `#cccbc8` | Borders, hairlines |
| Sand | `#e3dacc` | Hairline borders, fills |
| Clay | `#d97757` | The one chromatic accent, lamps and editorial accents only |
| Clay Deep | `#c6613f` | Clay hover |
| Leather | `#3a2b1c` | Sidebar body (gradient `#4d3a26` to `#2e2113`) |
| Leather Text | `#f0e6d2` | Text on leather |
| Leather Muted | `#c9b8a3` | Muted text on leather (contrast-checked) |
| Brass | `#a08a6d` | Scrollbar thumbs, metal edges |
| Brass Light | `#d9bd85` | Scrollbar thumb highlight, lamp rims |
| Success | `#02a745` | Semantic green (gains, buys) |
| Error | `#a10214` | Semantic red (losses, sells) |

## Tokens — Typography

- Display: Anthropic Serif, weight 400, sizes 24px and 30px for section
  titles, up to 56-68px for the hero headline, line-height 1.08-1.2.
  Web fallback: Source Serif 4, Charter, Georgia.
- UI: Anthropic Sans, weights 400-580, sizes 11-24px, line-height 1.33-1.63.
  Web fallback: Inter, IBM Plex Sans, system-ui. Weight 580 is the heaviest;
  never use 600+ for headlines, and never bold the serif.

## Materials (index.css)

- `.skeuo-metal` — Brushed metal: 8-stop vertical gradient plus fine
  horizontal hairlines, top highlight, bottom shade. Top bar, rails, knobs.
- `.skeuo-leather` — Sidebar body: warm brown gradient + SVG grain
  (feTurbulence), inset top highlight, deep bottom shade. Always paired
  with `.skeuo-stitch` (dashed inner frame, 7px inset).
- `.card` — Paper sheet: parchment gradient face, engraved top edge,
  three-layer drop shadow, 20px radius. Hover lifts 4px.
- `.skeuo-key` — Physical nav key: raised face, top highlight, bottom
  shade, 44px min height. Active state is pressed-in (inset shadow)
  with a clay `.skeuo-lamp` dot. Press sinks 1px.
- `.skeuo-medallion` — Metal icon tile: radial brass gradient, ring,
  inset shade. Active takes the clay radial.
- `.skeuo-knob` — Round metal knob: collapse, hamburger, close.
- `.skeuo-input` — Inset search well: pale gradient, inner shadow,
  clay focus ring.
- `.skeuo-lamp` — Brass-rimmed glowing dot: active indicator, LIVE.
- `.skeuo-scroll` — Visible brass scrollbar on dark (sidebar nav).
  Global scrollbars are thin brass on paper; 6px on mobile.
- `.tw-sidebar-shell` — Mobile: fixed left drawer, slides in 380ms.
  Desktop (md+): vertically centered floating rail, always visible.

## Tokens — Spacing & Shapes

- 64-80px between major sections, 32px card padding (24px on mobile),
  8-12px between elements inside a component.
- Radii: 20px paper cards, 22px sidebar, 12px keys and inputs,
  10px dark buttons, full rounds only for pills, lamps and knobs.
- Depth is layered shadows, never a single hard shadow. Pressed states
  use inset shadows. No flat surfaces on chrome; data tables stay flat
  and quiet so numbers stay legible.

## Guidelines

Do:
- Use Bone Parchment as the default page canvas.
- Set display headlines in the serif at weight 400 and let the serif do the work.
- Keep the palette monochrome; Clay is the only chromatic color.
- Pair Carbon Ink text with Paper White cards on Bone Parchment.
- Actions stay dark on light (ink key, parchment text). Clay never fills a button.
- Keep skeuomorphism on the chrome (sidebar, top bar, keys, inputs).
  Data stays dense and legible; never texture a table or a chart.
- Touch targets are 44px minimum on mobile (nav keys, knobs, star).

Don't:
- Don't introduce a second chromatic color for emphasis.
- Don't use pure black for body text.
- Don't mix flat and skeuomorphic randomly on the same component.
- Don't texture tables, charts, or numbers.
- Don't hide scrollbars on mobile; style them thin and visible.
- Don't use emoji as icons (SVG only).

## Mobile

- One menu only: the hamburger opens the sidebar as a slide-in drawer
  (300px, max 84vw). The old scrolling pill row is gone.
- Drawer closes on backdrop tap, Escape, the knob, or any nav tap.
- Body scroll locks while the drawer is open; drawer scroll is
  contained (overscroll-behavior: contain).
- No horizontal page scroll: `overflow-x: clip` on html/body and the
  app root. Tables scroll inside their own `overflow-x-auto` wrappers.
- Top bar respects the notch safe area (env safe-area-inset-top).
- Breakpoints to check: 375px, 768px, 1024px, 1440px.

## Motion (DesignSpells recipes + skeuo tactile)

- Animated numbers on KPI/index values: tween from the previous value over
  ~600ms, cubic ease-out, tabular numerals. Honors reduced-motion.
- Card hover: lift 4px, shadow deepens over 350ms.
- 3D tilt on dashboard cards (index strip, strong buys, movers, breadth):
  cards follow the cursor by at most 4 degrees with a 4px translateZ and
  the card's own soft shadow. No glare, no deep shadow, no tilt on the news
  card or hero text. Honors reduced-motion.
- Page reveal: fade + 12px rise over 0.6s, staggered 70ms per item, no blur.
- Sidebar: 500ms width transition with staggered label fade-in (kept).
- Drawer: 380ms slide, cubic-bezier(0.22,1,0.36,1). Keys press in 300ms.
- Focus is always visible (2px clay outline). Reduced-motion disables it all.

## Hero pattern (Supahero)

One headline, one supporting line, one primary action, one strong visual.
On the dashboard the visual is the live index strip, with serif numerals.

## Implementation note

The Tailwind config maps the old dark-theme class names onto these tokens
(ink scale now holds warm light surfaces, slate holds warm ink text), so the
170+ existing usages flip with the tokens. See tailwind.config.js. New code
should use the semantic names (paper, ivory, clay, slate-100) directly.
Skeuomorphic materials live in src/index.css, not in Tailwind config.
