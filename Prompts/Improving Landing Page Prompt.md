# Add Legal Links to the Footer

## Context

This is a Flask web app called **Spendly** — a personal expense tracker. It uses Jinja2 templates and a custom CSS design system with CSS variables. All pages share a single base template (`base.html`) that contains the site-wide header and footer.

The goal is to add **Terms and Conditions** and **Privacy Policy** links to the existing footer. The pages these links would point to do not exist yet, so the links must use placeholder `href="#"` values for now. The styling must visually match the rest of the footer.

---

## Files to Modify

| File | Purpose |
|---|---|
| `expense-tracker/templates/base.html` | Shared layout — contains the `<footer>` rendered on every page |
| `expense-tracker/static/css/style.css` | All custom styles |

---

## Current Footer HTML (`base.html`, inside `<body>`)

```html
<footer class="footer">
    <div class="footer-inner">
        <span class="brand-icon">◈</span>
        <span class="footer-name">Spendly</span>
        <p class="footer-copy">Track every rupee. Own your finances.</p>
    </div>
</footer>
```

---

## Current Footer CSS (`style.css`)

```css
.footer {
    background: var(--ink);
    color: var(--paper);
    padding: 2.5rem 2rem;
    text-align: center;
}

.footer-inner {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.4rem;
}

.footer .brand-icon { color: var(--accent-2); font-size: 1.5rem; }

.footer-name {
    font-weight: 600;
    font-size: 1rem;
}

.footer-copy {
    font-size: 0.8rem;
    color: var(--ink-faint);
}
```

---

## Relevant CSS Variables

```css
--ink:        #0f0f0f;   /* footer background */
--paper:      #f7f6f3;   /* default text on dark backgrounds */
--ink-faint:  #a0a0a0;   /* muted text — used by .footer-copy */
```

---

## What to Implement

### 1. HTML change (`base.html`)

Add a `<div class="footer-links">` directly after `.footer-copy`, still inside `.footer-inner`:

```html
<div class="footer-links">
    <a href="#" class="footer-link">Terms and Conditions</a>
    <span class="footer-link-sep">·</span>
    <a href="#" class="footer-link">Privacy Policy</a>
</div>
```

- Both `href` values must be `"#"` — the destination pages have not been built yet.
- Do **not** add Flask `url_for()` calls or create any new routes or templates.

### 2. CSS change (`style.css`)

Add the following rules after the `.footer-copy` block:

```css
.footer-links {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8rem;
}

.footer-link {
    color: var(--ink-faint);
    text-decoration: none;
}

.footer-link:hover { text-decoration: underline; }

.footer-link-sep {
    color: var(--ink-faint);
    user-select: none;
}
```

---

## Constraints

- Do **not** change any existing CSS rules — only append new ones.
- Do **not** alter the overall footer layout or visual hierarchy.
- Do **not** add JavaScript.
- The footer is already centered and stacks vertically via flexbox; the new links row must follow the same pattern and look correct at all viewport widths.
- Do **not** create route handlers, page templates, or blueprint files for Terms/Privacy pages.

---

## How to Verify

1. Run the Flask development server.
2. Open the landing page in a browser.
3. Scroll to the footer and confirm:
   - "Terms and Conditions" and "Privacy Policy" appear below the tagline.
   - Both links are separated by a `·` character.
   - Text color, size, and weight visually match the existing `.footer-copy` text.
   - Hovering either link shows an underline.
   - Clicking either link goes nowhere (stays on the same page — `href="#"` behavior).
4. Resize the browser to a narrow viewport (< 400 px) and confirm the links wrap or stay readable without breaking the layout.
