### token-b-tok2 + regex [personal only] on test (500 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 0.525 | 0.831 | 0.643 |
| Findings, text only | 0.547 | 0.868 | 0.671 |
| Prompt level (any sensitive info?) | 0.490 | 0.828 | 0.616 |

False alarm rate on clean prompts: 0.197 (407 clean, 93 sensitive). Tier accuracy on found items: 0.958. Recall by tier (1 low, 2 medium, 3 high): 1=0.977, 2=0.8983, 3=0.0. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| DATE_OF_BIRTH | 25 | 0.758 | 1.000 | 0.862 |
| EMAIL | 10 | 0.769 | 1.000 | 0.870 |
| GOV_ID | 20 | 0.000 | 0.000 | 0.000 |
| HOME_ADDRESS | 14 | 1.000 | 1.000 | 1.000 |
| PERSON_NAME | 77 | 0.819 | 1.000 | 0.901 |
| PHONE | 10 | 0.148 | 0.400 | 0.216 |
| WORKPLACE_SCHOOL | 10 | 0.471 | 0.800 | 0.593 |

Valid output: 1.000. Time: 0.015 s per prompt.
