### oracle on test (500 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 1.000 | 1.000 | 1.000 |
| Findings, text only | 1.000 | 1.000 | 1.000 |
| Prompt level (any sensitive info?) | 1.000 | 1.000 | 1.000 |

False alarm rate on clean prompts: 0.000 (204 clean, 296 sensitive). Tier accuracy on found items: 1.000. Recall by tier (1 low, 2 medium, 3 high): 1=1.0, 2=1.0, 3=1.0. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| BALANCE_DEBT | 30 | 1.000 | 1.000 | 1.000 |
| BANK_ACCOUNT | 31 | 1.000 | 1.000 | 1.000 |
| CARD_NUMBER | 25 | 1.000 | 1.000 | 1.000 |
| CREDENTIAL | 46 | 1.000 | 1.000 | 1.000 |
| DATE_OF_BIRTH | 30 | 1.000 | 1.000 | 1.000 |
| EMAIL | 24 | 1.000 | 1.000 | 1.000 |
| FIN_INSTITUTION | 49 | 1.000 | 1.000 | 1.000 |
| GOV_ID | 19 | 1.000 | 1.000 | 1.000 |
| HOME_ADDRESS | 30 | 1.000 | 1.000 | 1.000 |
| INCOME | 30 | 1.000 | 1.000 | 1.000 |
| MEDICATION | 20 | 1.000 | 1.000 | 1.000 |
| MED_CONDITION | 87 | 1.000 | 1.000 | 1.000 |
| MED_PROVIDER | 28 | 1.000 | 1.000 | 1.000 |
| MED_RECORD_ID | 13 | 1.000 | 1.000 | 1.000 |
| PERSON_NAME | 94 | 1.000 | 1.000 | 1.000 |
| PHONE | 24 | 1.000 | 1.000 | 1.000 |
| SENSITIVE_HEALTH | 13 | 1.000 | 1.000 | 1.000 |
| WORKPLACE_SCHOOL | 24 | 1.000 | 1.000 | 1.000 |

Valid JSON: 1.000. Time: 0.0 s per prompt.
