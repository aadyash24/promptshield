### token-financial-augmented-cased [financial only] on test (500 prompts)

| Metric | Precision | Recall | F1 |
| --- | --- | --- | --- |
| Findings, category must match | 0.580 | 0.842 | 0.687 |
| Findings, text only | 0.580 | 0.842 | 0.687 |
| Prompt level (any sensitive info?) | 0.743 | 1.000 | 0.852 |

False alarm rate on clean prompts: 0.061 (425 clean, 75 sensitive). Tier accuracy on found items: 1.000. Recall by tier (1 low, 2 medium, 3 high): 1=0.4118, 2=0.975, 3=1.0. Hallucinated findings: 0.000.

| Category | Support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| BALANCE_DEBT | 20 | 0.905 | 0.950 | 0.927 |
| BANK_ACCOUNT | 20 | 0.952 | 1.000 | 0.976 |
| CARD_NUMBER | 7 | 1.000 | 1.000 | 1.000 |
| CREDENTIAL | 32 | 0.444 | 1.000 | 0.615 |
| FIN_INSTITUTION | 34 | 0.275 | 0.412 | 0.329 |
| INCOME | 20 | 0.952 | 1.000 | 0.976 |

Valid output: 1.000. Time: 0.022 s per prompt.
