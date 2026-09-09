## 2024-10-27 - Consistent Affordances on Interactive Cards
**Learning:** When using full elements (like `<article>`) as clickable cards for both mouse and keyboard users, two things are essential: 1) they must have `role="button"` for screen readers to recognize them properly, and 2) the interaction boundaries must be unified. In this app, one card allowed keyboard activation on the full card but restricted mouse clicks to a small inner span, confusing mouse users.
**Action:** Always ensure that when `tabindex="0"` and keyboard events are added to a card, the `onclick` handler and visual hover states (like `hover:bg-gray-50`) apply to the same outer element, and always include `role="button"`.

## 2026-09-09 - Focus indicators and ARIA labels on Interactive Cards
**Learning:** Using `focus-within` for interactive cards with `tabindex="0"` can cause the focus indicator to misfire if child elements receive focus, leading to a confusing visual experience. Additionally, elements that act as buttons should have action-oriented `aria-label`s (e.g., "Ver detalhes do processo...") rather than just describing the content.
**Action:** When creating interactive cards, use `focus:outline-none focus:ring-2 focus:ring-blue-500` instead of `focus-within:` to indicate keyboard focus properly. Always add action-oriented `aria-label`s to provide context for screen readers.
