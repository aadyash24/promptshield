### Qwen3-0.6B+b [medical only] on handwritten (54 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 0.800 | 0.800 | 0.800 |
| Findings, text only | 0.840 | 0.840 | 0.840 |
| Prompt level (any sensitive info?) | 0.933 | 0.875 | 0.903 |

False alarm rate on clean prompts: 0.026 (38 clean, 16 sensitive). Tier accuracy on found items: 0.952. Recall by tier (1 low, 2 medium, 3 high): 1=0.8333, 2=0.9, 3=0.6667. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| MEDICATION | 5 | 0.833 | 1.000 | 0.909 |
| MED_CONDITION | 5 | 0.667 | 0.800 | 0.727 |
| MED_PROVIDER | 6 | 1.000 | 0.833 | 0.909 |
| MED_RECORD_ID | 4 | 0.800 | 1.000 | 0.889 |
| SENSITIVE_HEALTH | 5 | 0.667 | 0.400 | 0.500 |

Valid output: 1.000. Time: 0.893 s per prompt.
