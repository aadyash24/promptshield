### token-b-tok2 + regex [medical only] on test (500 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 0.657 | 0.683 | 0.670 |
| Findings, text only | 0.754 | 0.785 | 0.769 |
| Prompt level (any sensitive info?) | 0.863 | 0.969 | 0.913 |

False alarm rate on clean prompts: 0.098 (305 clean, 195 sensitive). Tier accuracy on found items: 0.881. Recall by tier (1 low, 2 medium, 3 high): 1=0.9559, 2=0.8763, 3=0.2632. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| MEDICATION | 82 | 0.632 | 0.878 | 0.735 |
| MED_CONDITION | 112 | 0.583 | 0.875 | 0.700 |
| MED_PROVIDER | 68 | 0.956 | 0.956 | 0.956 |
| MED_RECORD_ID | 66 | 0.594 | 0.288 | 0.388 |
| SENSITIVE_HEALTH | 67 | 0.552 | 0.239 | 0.333 |

Valid output: 1.000. Time: 0.017 s per prompt.
