## 2024-10-27 - Consistent Affordances on Interactive Cards
**Learning:** When using full elements (like `<article>`) as clickable cards for both mouse and keyboard users, two things are essential: 1) they must have `role="button"` for screen readers to recognize them properly, and 2) the interaction boundaries must be unified. In this app, one card allowed keyboard activation on the full card but restricted mouse clicks to a small inner span, confusing mouse users.
**Action:** Always ensure that when `tabindex="0"` and keyboard events are added to a card, the `onclick` handler and visual hover states (like `hover:bg-gray-50`) apply to the same outer element, and always include `role="button"`.

## 2026-09-08 - Action-Oriented ARIA labels and Focus States
**Learning:** Interactive cards need action-oriented `aria-label`s (e.g. "Ver detalhes do processo...") to provide context for screen readers. Furthermore, `focus-within:` can misfire on child elements; using `focus:` styling (e.g., `focus:outline-none focus:ring-2`) properly indicates keyboard focus.
**Action:** Always use action-oriented `aria-label`s and prefer `focus:` over `focus-within:` on interactive cards.
