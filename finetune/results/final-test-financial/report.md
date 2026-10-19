### token-b-tok2 [financial only] on test (500 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 0.461 | 0.664 | 0.544 |
| Findings, text only | 0.503 | 0.724 | 0.594 |
| Prompt level (any sensitive info?) | 0.613 | 0.851 | 0.713 |

False alarm rate on clean prompts: 0.083 (433 clean, 67 sensitive). Tier accuracy on found items: 1.000. Recall by tier (1 low, 2 medium, 3 high): 1=0.48, 2=0.5278, 3=0.8364. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| BALANCE_DEBT | 18 | 0.514 | 1.000 | 0.679 |
| BANK_ACCOUNT | 15 | 0.441 | 1.000 | 0.612 |
| CARD_NUMBER | 8 | 0.000 | 0.000 | 0.000 |
| CREDENTIAL | 32 | 0.775 | 0.969 | 0.861 |
| FIN_INSTITUTION | 25 | 0.255 | 0.480 | 0.333 |
| INCOME | 18 | 0.091 | 0.056 | 0.069 |

Valid output: 1.000. Time: 0.014 s per prompt.
