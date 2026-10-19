### token-b-tok2 + regex on test (500 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 0.578 | 0.713 | 0.639 |
| Findings, text only | 0.689 | 0.849 | 0.761 |
| Prompt level (any sensitive info?) | 0.821 | 1.000 | 0.901 |

False alarm rate on clean prompts: 0.360 (189 clean, 311 sensitive). Tier accuracy on found items: 0.916. Recall by tier (1 low, 2 medium, 3 high): 1=0.9, 2=0.8374, 3=0.3798. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| BALANCE_DEBT | 18 | 0.514 | 1.000 | 0.679 |
| BANK_ACCOUNT | 15 | 0.348 | 0.533 | 0.421 |
| CARD_NUMBER | 8 | 1.000 | 0.625 | 0.769 |
| CREDENTIAL | 32 | 0.775 | 0.969 | 0.861 |
| DATE_OF_BIRTH | 25 | 0.758 | 1.000 | 0.862 |
| EMAIL | 10 | 0.769 | 1.000 | 0.870 |
| FIN_INSTITUTION | 25 | 0.255 | 0.480 | 0.333 |
| GOV_ID | 20 | 0.000 | 0.000 | 0.000 |
| HOME_ADDRESS | 14 | 1.000 | 1.000 | 1.000 |
| INCOME | 18 | 0.091 | 0.056 | 0.069 |
| MEDICATION | 82 | 0.632 | 0.878 | 0.735 |
| MED_CONDITION | 112 | 0.583 | 0.875 | 0.700 |
| MED_PROVIDER | 68 | 0.956 | 0.956 | 0.956 |
| MED_RECORD_ID | 66 | 0.594 | 0.288 | 0.388 |
| PERSON_NAME | 77 | 0.819 | 1.000 | 0.901 |
| PHONE | 10 | 0.148 | 0.400 | 0.216 |
| SENSITIVE_HEALTH | 67 | 0.552 | 0.239 | 0.333 |
| WORKPLACE_SCHOOL | 10 | 0.471 | 0.800 | 0.593 |

Valid output: 1.000. Time: 0.016 s per prompt.
