### token-b-tok2 [medical only] on test (500 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 0.648 | 0.815 | 0.722 |
| Findings, text only | 0.722 | 0.909 | 0.805 |
| Prompt level (any sensitive info?) | 0.781 | 0.969 | 0.865 |

False alarm rate on clean prompts: 0.174 (305 clean, 195 sensitive). Tier accuracy on found items: 0.897. Recall by tier (1 low, 2 medium, 3 high): 1=0.9559, 2=0.8918, 3=0.6316. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| MEDICATION | 82 | 0.630 | 0.915 | 0.746 |
| MED_CONDITION | 112 | 0.567 | 0.875 | 0.688 |
| MED_PROVIDER | 68 | 0.915 | 0.956 | 0.935 |
| MED_RECORD_ID | 66 | 0.647 | 1.000 | 0.786 |
| SENSITIVE_HEALTH | 67 | 0.562 | 0.269 | 0.364 |

Valid output: 1.000. Time: 0.016 s per prompt.
