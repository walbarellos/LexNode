## 2024-10-27 - Consistent Affordances on Interactive Cards
**Learning:** When using full elements (like `<article>`) as clickable cards for both mouse and keyboard users, two things are essential: 1) they must have `role="button"` for screen readers to recognize them properly, and 2) the interaction boundaries must be unified. In this app, one card allowed keyboard activation on the full card but restricted mouse clicks to a small inner span, confusing mouse users.
**Action:** Always ensure that when `tabindex="0"` and keyboard events are added to a card, the `onclick` handler and visual hover states (like `hover:bg-gray-50`) apply to the same outer element, and always include `role="button"`.

## 2026-09-07 - Focus styling and ARIA labels on Interactive Cards
**Learning:** Using `focus-within:` on interactive cards containing text or multiple elements can cause focus styles to trigger unexpectedly when a user clicks or navigates inside the card. Also, generic `aria-label`s like "Processo 123" lack context for screen reader users on what action the card performs.
**Action:** Use direct focus styling like `focus:outline-none focus:ring-2` on the outer card element instead of `focus-within:`, and ensure `aria-label`s are action-oriented (e.g., "Ver detalhes do processo 123") to provide clear context for assistive technologies.
