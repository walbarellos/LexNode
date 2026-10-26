## 2024-10-27 - Consistent Affordances on Interactive Cards
**Learning:** When using full elements (like `<article>`) as clickable cards for both mouse and keyboard users, two things are essential: 1) they must have `role="button"` for screen readers to recognize them properly, and 2) the interaction boundaries must be unified. In this app, one card allowed keyboard activation on the full card but restricted mouse clicks to a small inner span, confusing mouse users.
**Action:** Always ensure that when `tabindex="0"` and keyboard events are added to a card, the `onclick` handler and visual hover states (like `hover:bg-gray-50`) apply to the same outer element, and always include `role="button"`.

## 2026-10-26 - Pseudo-Element Pattern for Clickable Cards
**Learning:** To make entire UI cards clickable while maintaining accessibility, it's problematic to add `role="button"` to the outer wrapper because screen readers will ignore the inner content (like links and lists). The pseudo-element overlay CSS pattern solves this effectively.
**Action:** Keep the semantic `<button>` or `<a>` inside the card, apply `position: relative` to the outer card wrapper, and add `::before { content: ''; position: absolute; inset: 0; }` to the button so its clickable area stretches to cover the entire card.
