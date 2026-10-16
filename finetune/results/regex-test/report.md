### regex on test (500 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 0.754 | 0.154 | 0.256 |
| Findings, text only | 0.897 | 0.183 | 0.304 |
| Prompt level (any sensitive info?) | 1.000 | 0.345 | 0.513 |

False alarm rate on clean prompts: 0.000 (204 clean, 296 sensitive). Tier accuracy on found items: 0.885. Recall by tier (1 low, 2 medium, 3 high): 1=0.0, 2=0.1745, 3=0.3197. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| BALANCE_DEBT | 30 | 0.000 | 0.000 | 0.000 |
| BANK_ACCOUNT | 31 | 0.000 | 0.000 | 0.000 |
| CARD_NUMBER | 25 | 1.000 | 1.000 | 1.000 |
| CREDENTIAL | 46 | 1.000 | 0.478 | 0.647 |
| DATE_OF_BIRTH | 30 | 0.000 | 0.000 | 0.000 |
| EMAIL | 24 | 1.000 | 1.000 | 1.000 |
| FIN_INSTITUTION | 49 | 0.000 | 0.000 | 0.000 |
| GOV_ID | 19 | 0.000 | 0.000 | 0.000 |
| HOME_ADDRESS | 30 | 0.000 | 0.000 | 0.000 |
| INCOME | 30 | 0.000 | 0.000 | 0.000 |
| MEDICATION | 20 | 0.000 | 0.000 | 0.000 |
| MED_CONDITION | 87 | 0.000 | 0.000 | 0.000 |
| MED_PROVIDER | 28 | 0.000 | 0.000 | 0.000 |
| MED_RECORD_ID | 13 | 0.000 | 0.000 | 0.000 |
| PERSON_NAME | 94 | 0.000 | 0.000 | 0.000 |
| PHONE | 24 | 0.649 | 1.000 | 0.787 |
| SENSITIVE_HEALTH | 13 | 0.000 | 0.000 | 0.000 |
| WORKPLACE_SCHOOL | 24 | 0.000 | 0.000 | 0.000 |

Valid JSON: 1.000. Time: 0.0 s per prompt.
