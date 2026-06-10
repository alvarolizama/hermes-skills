---
# Diseño UI para PocketBrain — Referencias de Design Systems

## Apple Design System (2026) aplicado a PocketBrain

### Tokens principales

| Token | Día (#hex) | Noche (#hex) | Uso |
|-------|-----------|-------------|-----|
| `--primary` | #0066cc | #2997ff | Links, botones, acento interactivo |
| `--primary-focus` | #0071e3 | #2997ff | Hover/focus de botones |
| `--ink` | #1d1d1f | #f5f5f7 | Textos principales |
| `--body-text` | #1d1d1f | #cccccc | Body copy |
| `--body-muted` | #7a7a7a | #7a7a7a | Texto secundario |
| `--canvas` | #ffffff | #1d1d1f | Fondo principal (cards) |
| `--canvas-parchment` | #f5f5f7 | #000000 | Fondo área de contenido |
| `--surface-pearl` | #fafafc | #2a2a2c | Fondo sidebar, hover |
| `--hairline` | #e0e0e0 | #333333 | Bordes, divisores |
| `--divider-soft` | #f0f0f0 | #2a2a2c | Bordes sutiles |

### Tipografía Apple en CSS

```css
/* Headings: SF Pro Display, tracking apretado */
font-family: SF Pro Display, system-ui, -apple-system, sans-serif;
/* Body: SF Pro Text, 17px (Apple default, no 16px) */
font-family: SF Pro Text, system-ui, -apple-system, sans-serif;
```

**Jerarquía:**
- H1 (view header): 40px / 600 / line-height 1.1 / letter-spacing 0
- H2 (sección): 28px / 600 / line-height 1.14 / letter-spacing 0  
- H3 (card title): 21px / 600 / line-height 1.19 / letter-spacing 0.231px
- Body: 17px / 400 / line-height 1.47 / letter-spacing -0.374px
- Caption (meta): 14px / 400 / line-height 1.43 / letter-spacing -0.224px
- Nav link: 12px / 400 / line-height 1.0 / letter-spacing 0.12px

### Componentes

#### Cards
- `border-radius: 18px` (rounded.lg)
- `border: 1px solid var(--hairline)`
- `padding: 24px`
- `background: var(--canvas)`
- Hover: `border-color: var(--divider-soft)` + `transform: translateY(-2px)`
- Sin sombras. Nunca.

#### Buttons (CTA primario)
- `background: var(--primary)`
- `color: #ffffff`
- `border-radius: 9999px` (pill completa)
- `padding: 11px 22px`
- Active: `transform: scale(0.95)` (micro-interacción Apple universal)
- Hover: `background: var(--primary-focus)`

#### Select / Input
- `border-radius: 8px` (no pill para inputs)
- `border: 1px solid var(--hairline)`
- Focus: `border-color: var(--primary)`
- Height: 44px (touch target Apple)

#### Tabs
- `border-bottom: 1px solid var(--hairline)` en el contenedor
- Active: `font-weight: 600`, `color: var(--primary)`, `border-bottom: 2px solid var(--primary)`
- Inactive: `color: var(--muted-48)`
- Sticky: `position: sticky`, `top: 0`, `backdrop-filter: blur(20px)`

#### Sidebar
- `width: 260px`, `padding: 20px 16px`
- Título con línea divisora: `border-bottom: 1px solid var(--hairline)`
- Nav links: `padding: 6px 10px`, `border-radius: 8px`
- Active: `background: var(--surface-pearl)`
- Night toggle al final (antes del status)

### Dark/Light toggle
- `localStorage` persiste: `pocketbrain-dark`
- Body class: `light` (default) o `night`
- Toggle en sidebar: cambia texto a `☀️ Día` o `🌙 Noche`
- Cambia todos los CSS variables vía clases anidadas en `:root` y `body.night`

### Animaciones
- Fade-in de vistas: `animation: fade 0.3s ease-out` (opacity + translateY 8px)
- Transiciones: `transition: all 0.15s` en botones, links, cards
- Cubic-bezier: `0.25, 0.1, 0.25, 1` (Apple easing)
