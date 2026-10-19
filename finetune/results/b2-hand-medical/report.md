### Qwen3-0.6B+b2 [medical only] on handwritten (54 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 0.880 | 0.880 | 0.880 |
| Findings, text only | 0.920 | 0.920 | 0.920 |
| Prompt level (any sensitive info?) | 1.000 | 0.938 | 0.968 |

False alarm rate on clean prompts: 0.000 (38 clean, 16 sensitive). Tier accuracy on found items: 0.957. Recall by tier (1 somewhat sensitive, 2 very sensitive): 1=0.9375, 2=0.7778. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| MEDICATION | 5 | 1.000 | 1.000 | 1.000 |
| MED_CONDITION | 5 | 0.667 | 0.800 | 0.727 |
| MED_PROVIDER | 6 | 1.000 | 1.000 | 1.000 |
| MED_RECORD_ID | 4 | 1.000 | 1.000 | 1.000 |
| SENSITIVE_HEALTH | 5 | 0.750 | 0.600 | 0.667 |

Valid output: 1.000. Time: 0.897 s per prompt.
