## 2024-10-27 - Consistent Affordances on Interactive Cards
**Learning:** When using full elements (like `<article>`) as clickable cards for both mouse and keyboard users, two things are essential: 1) they must have `role="button"` for screen readers to recognize them properly, and 2) the interaction boundaries must be unified. In this app, one card allowed keyboard activation on the full card but restricted mouse clicks to a small inner span, confusing mouse users.
**Action:** Always ensure that when `tabindex="0"` and keyboard events are added to a card, the `onclick` handler and visual hover states (like `hover:bg-gray-50`) apply to the same outer element, and always include `role="button"`.

## $(date +%Y-%m-%d) - Interactive Card Focus and Action-Oriented ARIA Labels
**Learning:** Using `focus-within:` on interactive cards can cause focus rings to appear unexpectedly when child elements receive focus, or fail to show properly when the card itself receives keyboard focus. Furthermore, `aria-label`s on clickable cards should describe the action ("Ver detalhes do processo..."), not just the content.
**Action:** Use `focus:` pseudo-classes (e.g. `focus:outline-none focus:ring-2`) directly on the clickable outer element (`<article role="button" tabindex="0">`) and ensure its `aria-label` starts with an actionable verb.
