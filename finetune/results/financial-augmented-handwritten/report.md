### token-financial-augmented-cased [financial only] on handwritten (69 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 0.615 | 0.762 | 0.681 |
| Findings, text only | 0.654 | 0.809 | 0.723 |
| Prompt level (any sensitive info?) | 0.818 | 0.947 | 0.878 |

False alarm rate on clean prompts: 0.080 (50 clean, 19 sensitive). Tier accuracy on found items: 1.000. Recall by tier (1 low, 2 medium, 3 high): 1=0.75, 2=0.75, 3=0.7778. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| BALANCE_DEBT | 4 | 0.600 | 0.750 | 0.667 |
| BANK_ACCOUNT | 2 | 1.000 | 0.500 | 0.667 |
| CARD_NUMBER | 3 | 1.000 | 1.000 | 1.000 |
| CREDENTIAL | 4 | 0.500 | 0.750 | 0.600 |
| FIN_INSTITUTION | 4 | 0.429 | 0.750 | 0.545 |
| INCOME | 4 | 0.750 | 0.750 | 0.750 |

Valid output: 1.000. Time: 0.091 s per prompt.
