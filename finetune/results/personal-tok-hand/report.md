### token-personal-tok [personal only] on handwritten (69 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 0.644 | 0.844 | 0.731 |
| Findings, text only | 0.678 | 0.889 | 0.769 |
| Prompt level (any sensitive info?) | 0.742 | 1.000 | 0.852 |

False alarm rate on clean prompts: 0.174 (46 clean, 23 sensitive). Tier accuracy on found items: 0.950. Recall by tier (1 low, 2 medium, 3 high): 1=0.8182, 2=1.0, 3=0.4. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| DATE_OF_BIRTH | 5 | 0.833 | 1.000 | 0.909 |
| EMAIL | 4 | 0.800 | 1.000 | 0.889 |
| GOV_ID | 5 | 0.667 | 0.400 | 0.500 |
| HOME_ADDRESS | 4 | 0.667 | 1.000 | 0.800 |
| PERSON_NAME | 15 | 0.684 | 0.867 | 0.765 |
| PHONE | 5 | 0.625 | 1.000 | 0.769 |
| WORKPLACE_SCHOOL | 7 | 0.417 | 0.714 | 0.526 |

Valid output: 1.000. Time: 0.109 s per prompt.
