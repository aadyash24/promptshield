### token-b-tok2 [medical only] on handwritten (84 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 0.590 | 0.920 | 0.719 |
| Findings, text only | 0.615 | 0.960 | 0.750 |
| Prompt level (any sensitive info?) | 0.696 | 1.000 | 0.821 |

False alarm rate on clean prompts: 0.103 (68 clean, 16 sensitive). Tier accuracy on found items: 0.958. Recall by tier (1 low, 2 medium, 3 high): 1=1.0, 2=0.9, 3=0.8889. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| MEDICATION | 5 | 0.625 | 1.000 | 0.769 |
| MED_CONDITION | 5 | 0.500 | 0.800 | 0.615 |
| MED_PROVIDER | 6 | 0.857 | 1.000 | 0.923 |
| MED_RECORD_ID | 4 | 0.364 | 1.000 | 0.533 |
| SENSITIVE_HEALTH | 5 | 0.800 | 0.800 | 0.800 |

Valid output: 1.000. Time: 0.076 s per prompt.
