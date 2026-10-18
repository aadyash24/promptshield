### regex [personal only] on test (500 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 0.433 | 0.165 | 0.239 |
| Findings, text only | 0.433 | 0.165 | 0.239 |
| Prompt level (any sensitive info?) | 0.569 | 0.342 | 0.427 |

False alarm rate on clean prompts: 0.082 (380 clean, 120 sensitive). Tier accuracy on found items: 1.000. Recall by tier (1 low, 2 medium, 3 high): 1=0.0, 2=0.3925, 3=0.0. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| DATE_OF_BIRTH | 40 | 0.000 | 0.000 | 0.000 |
| EMAIL | 21 | 1.000 | 1.000 | 1.000 |
| GOV_ID | 18 | 0.000 | 0.000 | 0.000 |
| HOME_ADDRESS | 25 | 0.000 | 0.000 | 0.000 |
| PERSON_NAME | 108 | 0.000 | 0.000 | 0.000 |
| PHONE | 21 | 0.840 | 1.000 | 0.913 |
| WORKPLACE_SCHOOL | 21 | 0.000 | 0.000 | 0.000 |

Valid output: 1.000. Time: 0.0 s per prompt.
