### token-personal-tok [personal only] on test (500 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 0.599 | 0.736 | 0.661 |
| Findings, text only | 0.647 | 0.795 | 0.714 |
| Prompt level (any sensitive info?) | 0.633 | 0.850 | 0.726 |

False alarm rate on clean prompts: 0.155 (380 clean, 120 sensitive). Tier accuracy on found items: 0.990. Recall by tier (1 low, 2 medium, 3 high): 1=0.6667, 2=0.9439, 3=0.0. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| DATE_OF_BIRTH | 40 | 0.851 | 1.000 | 0.919 |
| EMAIL | 21 | 0.955 | 1.000 | 0.977 |
| GOV_ID | 18 | 0.000 | 0.000 | 0.000 |
| HOME_ADDRESS | 25 | 0.962 | 1.000 | 0.980 |
| PERSON_NAME | 108 | 0.562 | 0.796 | 0.659 |
| PHONE | 21 | 0.714 | 0.714 | 0.714 |
| WORKPLACE_SCHOOL | 21 | 0.000 | 0.000 | 0.000 |

Valid output: 1.000. Time: 0.017 s per prompt.
