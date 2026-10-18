## 2024-10-27 - Consistent Affordances on Interactive Cards
**Learning:** When using full elements (like `<article>`) as clickable cards for both mouse and keyboard users, two things are essential: 1) they must have `role="button"` for screen readers to recognize them properly, and 2) the interaction boundaries must be unified. In this app, one card allowed keyboard activation on the full card but restricted mouse clicks to a small inner span, confusing mouse users.
**Action:** Always ensure that when `tabindex="0"` and keyboard events are added to a card, the `onclick` handler and visual hover states (like `hover:bg-gray-50`) apply to the same outer element, and always include `role="button"`.

## 2024-10-28 - Clickable Card Overlay Pseudo-Element Pattern
**Learning:** To make entire UI cards clickable while maintaining semantic meaning and keyboard focusability for screen readers, the pseudo-element overlay pattern is highly effective. Adding `role="button"` to the outer wrapper is an anti-pattern as it causes screen readers to ignore inner text elements.
**Action:** Use a semantic `<button>` inside the card. Apply `position: relative` to the card wrapper. Then, use `::before { content: ''; position: absolute; inset: 0; }` on the inner button to expand its clickable area to cover the entire card wrapper.
