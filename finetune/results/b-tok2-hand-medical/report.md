### token-b-tok2 [medical only] on handwritten (54 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 0.719 | 0.920 | 0.807 |
| Findings, text only | 0.750 | 0.960 | 0.842 |
| Prompt level (any sensitive info?) | 0.842 | 1.000 | 0.914 |

False alarm rate on clean prompts: 0.079 (38 clean, 16 sensitive). Tier accuracy on found items: 0.958. Recall by tier (1 somewhat sensitive, 2 very sensitive): 1=0.9375, 2=0.8889. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| MEDICATION | 5 | 0.714 | 1.000 | 0.833 |
| MED_CONDITION | 5 | 0.571 | 0.800 | 0.667 |
| MED_PROVIDER | 6 | 0.857 | 1.000 | 0.923 |
| MED_RECORD_ID | 4 | 0.667 | 1.000 | 0.800 |
| SENSITIVE_HEALTH | 5 | 0.800 | 0.800 | 0.800 |

Valid output: 1.000. Time: 0.148 s per prompt.
