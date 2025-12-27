# VIBOTAJ Global Design System

## Color Palette

### Primary Colors
| Name | Hex | Usage |
|------|-----|-------|
| Navy Blue | `#0A2540` | Primary brand, headers, CTAs |
| Navy Light | `#1A3A5C` | Hover states, secondary elements |
| Navy Dark | `#061627` | Footer, dark sections |

### Secondary Colors
| Name | Hex | Usage |
|------|-----|-------|
| Gold | `#D4A853` | Accents, highlights, premium elements |
| Orange | `#E67E22` | CTAs, notifications, energy points |
| Orange Light | `#F39C12` | Hover states, warnings |

### Neutrals
| Name | Hex | Usage |
|------|-----|-------|
| White | `#FFFFFF` | Backgrounds, text on dark |
| Gray 50 | `#F8FAFC` | Light backgrounds |
| Gray 100 | `#F1F5F9` | Cards, borders |
| Gray 300 | `#CBD5E1` | Borders, dividers |
| Gray 500 | `#64748B` | Secondary text |
| Gray 700 | `#334155` | Body text |
| Gray 900 | `#0F172A` | Headings |

### Semantic Colors
| Name | Hex | Usage |
|------|-----|-------|
| Success | `#10B981` | Confirmations, delivered status |
| Error | `#EF4444` | Errors, alerts |
| Warning | `#F59E0B` | Warnings, pending status |
| Info | `#3B82F6` | Information, in-transit status |

---

## Typography

### Font Families
```css
--font-heading: 'Poppins', sans-serif;
--font-body: 'Inter', sans-serif;
```

### Type Scale
| Name | Size | Weight | Line Height | Usage |
|------|------|--------|-------------|-------|
| H1 | 48px / 3rem | 700 | 1.2 | Hero headlines |
| H2 | 36px / 2.25rem | 600 | 1.25 | Section titles |
| H3 | 24px / 1.5rem | 600 | 1.3 | Subsection titles |
| H4 | 20px / 1.25rem | 600 | 1.4 | Card titles |
| Body Large | 18px / 1.125rem | 400 | 1.6 | Intro paragraphs |
| Body | 16px / 1rem | 400 | 1.6 | Default text |
| Body Small | 14px / 0.875rem | 400 | 1.5 | Captions, labels |
| Caption | 12px / 0.75rem | 500 | 1.4 | Metadata, hints |

---

## Spacing System (8px Base)

| Token | Value | Usage |
|-------|-------|-------|
| `--space-1` | 8px | Tight spacing, inline elements |
| `--space-2` | 16px | Default component padding |
| `--space-3` | 24px | Card padding, form groups |
| `--space-4` | 32px | Section spacing |
| `--space-5` | 40px | Large gaps |
| `--space-6` | 48px | Section padding |
| `--space-8` | 64px | Major section breaks |
| `--space-10` | 80px | Hero sections |

---

## Button Styles

### Primary Button
```css
.btn-primary {
  background: #0A2540;
  color: #FFFFFF;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 16px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}
.btn-primary:hover {
  background: #1A3A5C;
  transform: translateY(-1px);
}
```

### Secondary Button
```css
.btn-secondary {
  background: transparent;
  color: #0A2540;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 16px;
  border: 2px solid #0A2540;
  cursor: pointer;
  transition: all 0.2s ease;
}
.btn-secondary:hover {
  background: #0A2540;
  color: #FFFFFF;
}
```

### Ghost Button
```css
.btn-ghost {
  background: transparent;
  color: #0A2540;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 16px;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}
.btn-ghost:hover {
  background: #F1F5F9;
}
```

### Button Sizes
| Size | Padding | Font Size |
|------|---------|-----------|
| Small | 8px 16px | 14px |
| Medium | 12px 24px | 16px |
| Large | 16px 32px | 18px |

---

## Form Input Styles

```css
.input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #CBD5E1;
  border-radius: 8px;
  font-size: 16px;
  font-family: 'Inter', sans-serif;
  background: #FFFFFF;
  color: #334155;
  transition: all 0.2s ease;
}
.input:focus {
  outline: none;
  border-color: #0A2540;
  box-shadow: 0 0 0 3px rgba(10, 37, 64, 0.1);
}
.input::placeholder {
  color: #64748B;
}
.input-error {
  border-color: #EF4444;
}
.input-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #334155;
  margin-bottom: 8px;
}
```

---

## Card Component

```css
.card {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #F1F5F9;
  transition: all 0.2s ease;
}
.card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}
.card-header {
  margin-bottom: 16px;
}
.card-title {
  font-size: 20px;
  font-weight: 600;
  color: #0F172A;
}
.card-body {
  color: #334155;
  line-height: 1.6;
}
```

### Card Variants
| Variant | Border | Background |
|---------|--------|------------|
| Default | `#F1F5F9` | `#FFFFFF` |
| Elevated | none | `#FFFFFF` + stronger shadow |
| Outlined | `#CBD5E1` | transparent |
| Featured | `#D4A853` left accent | `#FFFFFF` |

---

## Responsive Breakpoints

| Name | Min Width | Target Devices |
|------|-----------|----------------|
| Mobile | 0px | Phones (portrait) |
| Mobile Large | 480px | Phones (landscape) |
| Tablet | 768px | Tablets, small laptops |
| Desktop | 1024px | Laptops, desktops |
| Desktop Large | 1280px | Large monitors |
| Wide | 1536px | Ultra-wide displays |

### CSS Media Queries
```css
/* Mobile-first approach */
@media (min-width: 480px) { /* Mobile Large */ }
@media (min-width: 768px) { /* Tablet */ }
@media (min-width: 1024px) { /* Desktop */ }
@media (min-width: 1280px) { /* Desktop Large */ }
@media (min-width: 1536px) { /* Wide */ }
```

### Container Max Widths
| Breakpoint | Max Width |
|------------|-----------|
| Mobile | 100% (16px padding) |
| Tablet | 720px |
| Desktop | 960px |
| Desktop Large | 1140px |
| Wide | 1320px |

---

## Quick Reference

### CSS Variables
```css
:root {
  /* Colors */
  --color-primary: #0A2540;
  --color-secondary: #D4A853;
  --color-accent: #E67E22;
  
  /* Typography */
  --font-heading: 'Poppins', sans-serif;
  --font-body: 'Inter', sans-serif;
  
  /* Spacing */
  --space-unit: 8px;
  
  /* Border Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
}
```
