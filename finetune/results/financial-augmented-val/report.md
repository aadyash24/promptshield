### token-financial-augmented-cased [financial only] on val (300 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 1.000 | 1.000 | 1.000 |
| Findings, text only | 1.000 | 1.000 | 1.000 |
| Prompt level (any sensitive info?) | 1.000 | 1.000 | 1.000 |

False alarm rate on clean prompts: 0.000 (231 clean, 69 sensitive). Tier accuracy on found items: 1.000. Recall by tier (1 low, 2 medium, 3 high): 1=1.0, 2=1.0, 3=1.0. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| BALANCE_DEBT | 17 | 1.000 | 1.000 | 1.000 |
| BANK_ACCOUNT | 8 | 1.000 | 1.000 | 1.000 |
| CARD_NUMBER | 10 | 1.000 | 1.000 | 1.000 |
| CREDENTIAL | 29 | 1.000 | 1.000 | 1.000 |
| FIN_INSTITUTION | 3 | 1.000 | 1.000 | 1.000 |
| INCOME | 11 | 1.000 | 1.000 | 1.000 |

Valid output: 1.000. Time: 0.03 s per prompt.
