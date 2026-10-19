### token-personal-tok on val (300 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 1.000 | 1.000 | 1.000 |
| Findings, text only | 1.000 | 1.000 | 1.000 |
| Prompt level (any sensitive info?) | 1.000 | 1.000 | 1.000 |

False alarm rate on clean prompts: 0.000 (87 clean, 213 sensitive). Tier accuracy on found items: 1.000. Recall by tier (1 low, 2 medium, 3 high): 1=1.0, 2=1.0, 3=1.0. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| BALANCE_DEBT | 17 | 1.000 | 1.000 | 1.000 |
| BANK_ACCOUNT | 8 | 1.000 | 1.000 | 1.000 |
| CARD_NUMBER | 10 | 1.000 | 1.000 | 1.000 |
| CREDENTIAL | 29 | 1.000 | 1.000 | 1.000 |
| DATE_OF_BIRTH | 27 | 1.000 | 1.000 | 1.000 |
| EMAIL | 25 | 1.000 | 1.000 | 1.000 |
| FIN_INSTITUTION | 3 | 1.000 | 1.000 | 1.000 |
| GOV_ID | 23 | 1.000 | 1.000 | 1.000 |
| HOME_ADDRESS | 27 | 1.000 | 1.000 | 1.000 |
| INCOME | 11 | 1.000 | 1.000 | 1.000 |
| MEDICATION | 21 | 1.000 | 1.000 | 1.000 |
| MED_CONDITION | 33 | 1.000 | 1.000 | 1.000 |
| MED_PROVIDER | 24 | 1.000 | 1.000 | 1.000 |
| MED_RECORD_ID | 17 | 1.000 | 1.000 | 1.000 |
| PERSON_NAME | 82 | 1.000 | 1.000 | 1.000 |
| PHONE | 34 | 1.000 | 1.000 | 1.000 |
| SENSITIVE_HEALTH | 10 | 1.000 | 1.000 | 1.000 |
| WORKPLACE_SCHOOL | 22 | 1.000 | 1.000 | 1.000 |

Valid output: 1.000. Time: 0.027 s per prompt.
