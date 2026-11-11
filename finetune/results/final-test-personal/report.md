### token-b-tok2 [personal only] on test (500 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 0.682 | 0.813 | 0.742 |
| Findings, text only | 0.712 | 0.849 | 0.775 |
| Prompt level (any sensitive info?) | 0.694 | 0.828 | 0.755 |

False alarm rate on clean prompts: 0.084 (407 clean, 93 sensitive). Tier accuracy on found items: 0.957. Recall by tier (1 low, 2 medium, 3 high): 1=0.977, 2=0.8475, 3=0.0. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| DATE_OF_BIRTH | 25 | 0.758 | 1.000 | 0.862 |
| EMAIL | 10 | 0.769 | 1.000 | 0.870 |
| GOV_ID | 20 | 0.000 | 0.000 | 0.000 |
| HOME_ADDRESS | 14 | 1.000 | 1.000 | 1.000 |
| PERSON_NAME | 77 | 0.819 | 1.000 | 0.901 |
| PHONE | 10 | 0.056 | 0.100 | 0.071 |
| WORKPLACE_SCHOOL | 10 | 0.471 | 0.800 | 0.593 |

Valid output: 1.000. Time: 0.015 s per prompt.
