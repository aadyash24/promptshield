### token-b-tok2 [financial only] on handwritten (84 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 0.600 | 0.714 | 0.652 |
| Findings, text only | 0.680 | 0.809 | 0.739 |
| Prompt level (any sensitive info?) | 0.750 | 0.789 | 0.769 |

False alarm rate on clean prompts: 0.077 (65 clean, 19 sensitive). Tier accuracy on found items: 1.000. Recall by tier (1 low, 2 medium, 3 high): 1=1.0, 2=0.625, 3=0.6667. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| BALANCE_DEBT | 4 | 0.500 | 0.750 | 0.600 |
| BANK_ACCOUNT | 2 | 0.500 | 0.500 | 0.500 |
| CARD_NUMBER | 3 | 1.000 | 0.333 | 0.500 |
| CREDENTIAL | 4 | 1.000 | 1.000 | 1.000 |
| FIN_INSTITUTION | 4 | 0.667 | 1.000 | 0.800 |
| INCOME | 4 | 0.333 | 0.500 | 0.400 |

Valid output: 1.000. Time: 0.058 s per prompt.
