### token-b-tok2 [personal only] on handwritten (84 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 0.691 | 0.844 | 0.760 |
| Findings, text only | 0.709 | 0.867 | 0.780 |
| Prompt level (any sensitive info?) | 0.733 | 0.957 | 0.830 |

False alarm rate on clean prompts: 0.131 (61 clean, 23 sensitive). Tier accuracy on found items: 0.974. Recall by tier (1 low, 2 medium, 3 high): 1=0.8636, 2=0.9444, 3=0.4. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| DATE_OF_BIRTH | 5 | 0.833 | 1.000 | 0.909 |
| EMAIL | 4 | 0.500 | 0.750 | 0.600 |
| GOV_ID | 5 | 0.333 | 0.400 | 0.364 |
| HOME_ADDRESS | 4 | 1.000 | 1.000 | 1.000 |
| PERSON_NAME | 15 | 0.722 | 0.867 | 0.788 |
| PHONE | 5 | 0.625 | 1.000 | 0.769 |
| WORKPLACE_SCHOOL | 7 | 0.857 | 0.857 | 0.857 |

Valid output: 1.000. Time: 0.048 s per prompt.
