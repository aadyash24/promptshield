### token-b-tok [medical only] on handwritten (54 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 0.467 | 0.560 | 0.509 |
| Findings, text only | 0.533 | 0.640 | 0.582 |
| Prompt level (any sensitive info?) | 0.833 | 0.938 | 0.882 |

False alarm rate on clean prompts: 0.079 (38 clean, 16 sensitive). Tier accuracy on found items: 0.875. Recall by tier (1 low, 2 medium, 3 high): 1=0.1667, 2=0.8, 3=0.5556. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| MEDICATION | 5 | 0.500 | 0.800 | 0.615 |
| MED_CONDITION | 5 | 0.500 | 0.800 | 0.615 |
| MED_PROVIDER | 6 | 0.250 | 0.167 | 0.200 |
| MED_RECORD_ID | 4 | 0.429 | 0.750 | 0.545 |
| SENSITIVE_HEALTH | 5 | 0.667 | 0.400 | 0.500 |

Valid output: 1.000. Time: 0.154 s per prompt.
