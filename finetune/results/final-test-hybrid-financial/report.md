### token-b-tok2 + regex [financial only] on test (500 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 0.466 | 0.647 | 0.541 |
| Findings, text only | 0.509 | 0.707 | 0.592 |
| Prompt level (any sensitive info?) | 0.633 | 0.851 | 0.726 |

False alarm rate on clean prompts: 0.076 (433 clean, 67 sensitive). Tier accuracy on found items: 1.000. Recall by tier (1 low, 2 medium, 3 high): 1=0.48, 2=0.5278, 3=0.8. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| BALANCE_DEBT | 18 | 0.514 | 1.000 | 0.679 |
| BANK_ACCOUNT | 15 | 0.348 | 0.533 | 0.421 |
| CARD_NUMBER | 8 | 1.000 | 0.625 | 0.769 |
| CREDENTIAL | 32 | 0.775 | 0.969 | 0.861 |
| FIN_INSTITUTION | 25 | 0.255 | 0.480 | 0.333 |
| INCOME | 18 | 0.091 | 0.056 | 0.069 |

Valid output: 1.000. Time: 0.015 s per prompt.
