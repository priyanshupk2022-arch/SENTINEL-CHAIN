import re
from typing import Dict, List, Optional
from pydantic import BaseModel

class IntentMatch(BaseModel):
    is_match: bool
    categories: List[str]

class IntentFilter:
    def __init__(self):
        # High-performance local regex patterns
        self.churn_pattern = re.compile(r'\b(cancel|unsubscribe|moving to|switch to|hate|terrible|sucks|goodbye|leaving)\b', re.IGNORECASE)
        self.pricing_pattern = re.compile(r'\b(too expensive|pricey|cost too much|cant afford|rip off|discount|cheaper alternative)\b', re.IGNORECASE)
        self.feature_pattern = re.compile(r'\b(wish it had|missing|lack of|doesn\'t have|need|feature request|would be nice)\b', re.IGNORECASE)

    def analyze(self, text: str) -> IntentMatch:
        categories = []
        if self.churn_pattern.search(text):
            categories.append('churn')
        if self.pricing_pattern.search(text):
            categories.append('pricing')
        if self.feature_pattern.search(text):
            categories.append('feature_request')
        
        return IntentMatch(
            is_match=len(categories) > 0,
            categories=categories
        )

# Singleton instance
intent_filter = IntentFilter()
