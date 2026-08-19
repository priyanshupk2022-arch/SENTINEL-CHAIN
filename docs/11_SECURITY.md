# 11 SECURITY ARCHITECTURE
**Threat:** Prompt Injection from Target Website.
**Mitigation:** LLM Output -> Schema Validation -> Semantic Allowlist -> `asyncio.create_subprocess_exec("bdata", "scraper", "heal", id, "--", proposal.repair_prompt)`. (The `--` POSIX delimiter prevents Argument Injection if the LLM hallucinated a string starting with `-`).
**Invariant:** The system NEVER passes untrusted input to a shell interpreter.
