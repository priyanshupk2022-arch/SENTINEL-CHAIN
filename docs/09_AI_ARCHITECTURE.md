# 09 AI ARCHITECTURE
**Model:** Gemini 3.1 Pro (Multimodal).
**Responsibilities:** Diagnosing visual/DOM drift and generating a natural language repair instruction.
**Restrictions:** Cannot execute code. Cannot approve its own fixes without Pydantic validation.
**Input:** Pruned DOM + Accessibility Object Model (AOM) + Playwright Screenshot (Set-of-Mark).
**Output:** JSON matching `RepairProposal` schema.
