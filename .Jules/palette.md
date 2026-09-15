## 2024-10-27 - Consistent Affordances on Interactive Cards
**Learning:** When using full elements (like `<article>`) as clickable cards for both mouse and keyboard users, two things are essential: 1) they must have `role="button"` for screen readers to recognize them properly, and 2) the interaction boundaries must be unified. In this app, one card allowed keyboard activation on the full card but restricted mouse clicks to a small inner span, confusing mouse users.
**Action:** Always ensure that when `tabindex="0"` and keyboard events are added to a card, the `onclick` handler and visual hover states (like `hover:bg-gray-50`) apply to the same outer element, and always include `role="button"`.

## 2024-10-27 - Keyboard Focus States on Interactive Cards
**Learning:** Using `focus-within` on an interactive card (e.g., an `<article>` acting as a button) can lead to unintended visual focus rings if a child element accidentally receives focus, or it may not trigger correctly when the card itself is focused.
**Action:** Use direct focus pseudo-classes (e.g., `focus:outline-none focus:ring-2`) on the interactive element itself to ensure the focus ring accurately reflects the user's focus state.
