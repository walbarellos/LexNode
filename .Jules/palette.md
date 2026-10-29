## 2024-10-27 - Consistent Affordances on Interactive Cards
**Learning:** When using full elements (like `<article>`) as clickable cards for both mouse and keyboard users, two things are essential: 1) they must have `role="button"` for screen readers to recognize them properly, and 2) the interaction boundaries must be unified. In this app, one card allowed keyboard activation on the full card but restricted mouse clicks to a small inner span, confusing mouse users.
**Action:** Always ensure that when `tabindex="0"` and keyboard events are added to a card, the `onclick` handler and visual hover states (like `hover:bg-gray-50`) apply to the same outer element, and always include `role="button"`.

## 2024-10-27 - Full-Card Clickability via Pseudo-elements
**Learning:** Adding `role="button"` to a card's outer wrapper (`<article>` or `<li>`) makes the whole card clickable but causes screen readers to ignore inner interactive content (like semantic `<button>`s inside).
**Action:** Keep the semantic `<button>` inside the card, apply `position: relative` to the card wrapper, and use `::before { content: ''; position: absolute; inset: 0; }` on the button to stretch its click target over the whole card without breaking accessibility.
