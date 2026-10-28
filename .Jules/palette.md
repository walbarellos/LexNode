## 2024-10-27 - Consistent Affordances on Interactive Cards
**Learning:** When using full elements (like `<article>`) as clickable cards for both mouse and keyboard users, two things are essential: 1) they must have `role="button"` for screen readers to recognize them properly, and 2) the interaction boundaries must be unified. In this app, one card allowed keyboard activation on the full card but restricted mouse clicks to a small inner span, confusing mouse users.
**Action:** Always ensure that when `tabindex="0"` and keyboard events are added to a card, the `onclick` handler and visual hover states (like `hover:bg-gray-50`) apply to the same outer element, and always include `role="button"`.

## 2024-10-28 - Pseudo-element Overlay for Clickable Cards
**Learning:** Making entire cards clickable by adding `role="button"` to the outer wrapper is an anti-pattern because it causes screen readers to ignore the card's inner content (like text and secondary links).
**Action:** Instead, use the pseudo-element overlay pattern: place a semantic `<button>` inside the card, set the card wrapper to `position: relative`, and apply `::before { content: ''; position: absolute; inset: 0; }` to the button so its clickable area stretches to cover the entire card.
