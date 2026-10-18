### Qwen3-0.6B (zero-shot) [medical only] on val (100 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 0.000 | 0.000 | 0.000 |
| Findings, text only | 0.000 | 0.000 | 0.000 |
| Prompt level (any sensitive info?) | 0.500 | 0.037 | 0.069 |

False alarm rate on clean prompts: 0.014 (73 clean, 27 sensitive). Tier accuracy on found items: 0.000. Recall by tier (1 low, 2 medium, 3 high): 1=0.0, 2=0.0, 3=0.0. Hallucinated findings: 0.500.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| MEDICATION | 6 | 0.000 | 0.000 | 0.000 |
| MED_CONDITION | 16 | 0.000 | 0.000 | 0.000 |
| MED_PROVIDER | 17 | 0.000 | 0.000 | 0.000 |
| MED_RECORD_ID | 7 | 0.000 | 0.000 | 0.000 |
| SENSITIVE_HEALTH | 3 | 0.000 | 0.000 | 0.000 |

Valid output: 0.950. Time: 0.59 s per prompt.
