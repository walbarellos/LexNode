## 2024-10-27 - Consistent Affordances on Interactive Cards
**Learning:** When using full elements (like `<article>`) as clickable cards for both mouse and keyboard users, two things are essential: 1) they must have `role="button"` for screen readers to recognize them properly, and 2) the interaction boundaries must be unified. In this app, one card allowed keyboard activation on the full card but restricted mouse clicks to a small inner span, confusing mouse users.
**Action:** Always ensure that when `tabindex="0"` and keyboard events are added to a card, the `onclick` handler and visual hover states (like `hover:bg-gray-50`) apply to the same outer element, and always include `role="button"`.

## 2024-11-20 - Actionable ARIA Labels on Interactive Cards
**Learning:** Screen reader users need descriptive context for actions, especially on generic interactive elements like cards. Having an `aria-label` like "Processo 123" just announces the state, not the action. It's better to explicitly describe the action the interaction will perform.
**Action:** When creating custom interactive elements (like cards with `role="button"`), use action-oriented `aria-label`s like "Ver detalhes do processo 123" rather than just restating the content.
