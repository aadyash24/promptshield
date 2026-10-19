### oracle [medical only] on test (500 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 1.000 | 1.000 | 1.000 |
| Findings, text only | 1.000 | 1.000 | 1.000 |
| Prompt level (any sensitive info?) | 1.000 | 1.000 | 1.000 |

False alarm rate on clean prompts: 0.000 (309 clean, 191 sensitive). Tier accuracy on found items: 1.000. Recall by tier (1 low, 2 medium, 3 high): 1=1.0, 2=1.0, 3=1.0. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| MEDICATION | 84 | 1.000 | 1.000 | 1.000 |
| MED_CONDITION | 113 | 1.000 | 1.000 | 1.000 |
| MED_PROVIDER | 63 | 1.000 | 1.000 | 1.000 |
| MED_RECORD_ID | 66 | 1.000 | 1.000 | 1.000 |
| SENSITIVE_HEALTH | 67 | 1.000 | 1.000 | 1.000 |

Valid output: 1.000. Time: 0.0 s per prompt.
