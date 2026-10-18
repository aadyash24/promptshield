### token-b-tok [medical only] on val (300 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 1.000 | 1.000 | 1.000 |
| Findings, text only | 1.000 | 1.000 | 1.000 |
| Prompt level (any sensitive info?) | 1.000 | 1.000 | 1.000 |

False alarm rate on clean prompts: 0.000 (235 clean, 65 sensitive). Tier accuracy on found items: 1.000. Recall by tier (1 low, 2 medium, 3 high): 1=1.0, 2=1.0, 3=1.0. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| MEDICATION | 21 | 1.000 | 1.000 | 1.000 |
| MED_CONDITION | 33 | 1.000 | 1.000 | 1.000 |
| MED_PROVIDER | 24 | 1.000 | 1.000 | 1.000 |
| MED_RECORD_ID | 17 | 1.000 | 1.000 | 1.000 |
| SENSITIVE_HEALTH | 10 | 1.000 | 1.000 | 1.000 |

Valid output: 1.000. Time: 0.029 s per prompt.
