### token-b-tok [medical only] on handwritten (54 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 0.667 | 0.880 | 0.759 |
| Findings, text only | 0.697 | 0.920 | 0.793 |
| Prompt level (any sensitive info?) | 0.833 | 0.938 | 0.882 |

False alarm rate on clean prompts: 0.079 (38 clean, 16 sensitive). Tier accuracy on found items: 0.957. Recall by tier (1 low, 2 medium, 3 high): 1=0.8333, 2=1.0, 3=0.7778. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| MEDICATION | 5 | 0.714 | 1.000 | 0.833 |
| MED_CONDITION | 5 | 0.714 | 1.000 | 0.833 |
| MED_PROVIDER | 6 | 0.625 | 0.833 | 0.714 |
| MED_RECORD_ID | 4 | 0.667 | 1.000 | 0.800 |
| SENSITIVE_HEALTH | 5 | 0.600 | 0.600 | 0.600 |

Valid output: 1.000. Time: 0.149 s per prompt.
