### regex on handwritten (39 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 1.000 | 0.186 | 0.314 |
| Findings, text only | 1.000 | 0.186 | 0.314 |
| Prompt level (any sensitive info?) | 1.000 | 0.280 | 0.438 |

False alarm rate on clean prompts: 0.000 (14 clean, 25 sensitive). Tier accuracy on found items: 1.000. Recall by tier (1 low, 2 medium, 3 high): 1=0.0, 2=0.25, 3=0.3636. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| BALANCE_DEBT | 2 | 0.000 | 0.000 | 0.000 |
| CARD_NUMBER | 1 | 1.000 | 1.000 | 1.000 |
| CREDENTIAL | 4 | 1.000 | 0.500 | 0.667 |
| DATE_OF_BIRTH | 3 | 0.000 | 0.000 | 0.000 |
| EMAIL | 2 | 1.000 | 1.000 | 1.000 |
| FIN_INSTITUTION | 1 | 0.000 | 0.000 | 0.000 |
| GOV_ID | 2 | 1.000 | 0.500 | 0.667 |
| HOME_ADDRESS | 2 | 0.000 | 0.000 | 0.000 |
| INCOME | 2 | 0.000 | 0.000 | 0.000 |
| MEDICATION | 1 | 0.000 | 0.000 | 0.000 |
| MED_CONDITION | 2 | 0.000 | 0.000 | 0.000 |
| MED_PROVIDER | 3 | 0.000 | 0.000 | 0.000 |
| MED_RECORD_ID | 1 | 0.000 | 0.000 | 0.000 |
| PERSON_NAME | 8 | 0.000 | 0.000 | 0.000 |
| PHONE | 2 | 1.000 | 1.000 | 1.000 |
| SENSITIVE_HEALTH | 3 | 0.000 | 0.000 | 0.000 |
| WORKPLACE_SCHOOL | 4 | 0.000 | 0.000 | 0.000 |

Valid JSON: 1.000. Time: 0.0 s per prompt.
