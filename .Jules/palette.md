## 2024-11-20 - Button Feedback UX
**Learning:** For async actions, showing loading state directly on the triggering button (via spinner and text change like "Buscando...") provides much clearer and more immediate feedback than relying solely on global loading indicators below the fold. It prevents duplicate submissions inherently and clearly communicates system status.
**Action:** Always consider converting the submit button into a loading state (spinner + action text) during async form submissions.
