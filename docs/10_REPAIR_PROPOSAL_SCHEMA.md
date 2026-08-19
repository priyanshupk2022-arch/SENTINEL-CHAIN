# 10 REPAIR PROPOSAL SCHEMA
```python
class RepairProposal(BaseModel):
    diagnosis: str
    target_field: str
    evidence: str
    proposed_selector: str
    repair_prompt: str  # ONLY this field is passed to Bright Data CLI
    confidence: float   # Must be >= 0.8
    expected_output: str
```
