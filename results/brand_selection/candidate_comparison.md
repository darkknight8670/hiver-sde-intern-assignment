# Brand Selection Analysis

## Important methodology note

The Twitter Support dataset does not contain an explicit ground-truth resolution label. Therefore this analysis does not claim to measure true resolution rate. Metrics such as response rate and support engagement are observable proxies based on tweet relationships.

## Candidate Comparison

| brand           |   tweet_count |   customer_authors |   brand_authors |   support_interactions |   brand_responses |   response_rate |   multi_turn_rate |   usable_customer_messages |   empty_brand_message_rate |   short_brand_message_rate |   candidate_quality_score |   candidate_score |
|:----------------|--------------:|-------------------:|----------------:|-----------------------:|------------------:|----------------:|------------------:|---------------------------:|---------------------------:|---------------------------:|--------------------------:|------------------:|
| AmazonHelp      |        169840 |             702669 |               1 |                      0 |                 0 |               0 |                 0 |                    1531727 |                          0 |                     0.0002 |                       0.4 |            4.8165 |
| AppleSupport    |        106860 |             702669 |               1 |                      0 |                 0 |               0 |                 0 |                    1531727 |                          0 |                     0      |                       0.4 |            4.6317 |
| Uber_Support    |         56270 |             702669 |               1 |                      0 |                 0 |               0 |                 0 |                    1531727 |                          0 |                     0      |                       0.4 |            4.3751 |
| SpotifyCares    |         43265 |             702669 |               1 |                      0 |                 0 |               0 |                 0 |                    1531727 |                          0 |                     0      |                       0.4 |            4.27   |
| Delta           |         42253 |             702669 |               1 |                      0 |                 0 |               0 |                 0 |                    1531727 |                          0 |                     0      |                       0.4 |            4.2606 |
| Tesco           |         38573 |             702669 |               1 |                      0 |                 0 |               0 |                 0 |                    1531727 |                          0 |                     0.0001 |                       0.4 |            4.2239 |
| AmericanAir     |         36764 |             702669 |               1 |                      0 |                 0 |               0 |                 0 |                    1531727 |                          0 |                     0      |                       0.4 |            4.2049 |
| TMobileHelp     |         34317 |             702669 |               1 |                      0 |                 0 |               0 |                 0 |                    1531727 |                          0 |                     0      |                       0.4 |            4.1774 |
| comcastcares    |         33031 |             702669 |               1 |                      0 |                 0 |               0 |                 0 |                    1531727 |                          0 |                     0      |                       0.4 |            4.1621 |
| British_Airways |         29361 |             702669 |               1 |                      0 |                 0 |               0 |                 0 |                    1531727 |                          0 |                     0.0002 |                       0.4 |            4.1146 |

## Top 3 Candidates

### 1. AmazonHelp

- Tweets: 169,840
- Customer authors: 702,669
- Support interactions: 0
- Brand responses: 0
- Response rate: 0.00%
- Multi-turn rate: 0.00%
- Usable customer messages: 1,531,727
- Candidate score: 4.8165

### 2. AppleSupport

- Tweets: 106,860
- Customer authors: 702,669
- Support interactions: 0
- Brand responses: 0
- Response rate: 0.00%
- Multi-turn rate: 0.00%
- Usable customer messages: 1,531,727
- Candidate score: 4.6317

### 3. Uber_Support

- Tweets: 56,270
- Customer authors: 702,669
- Support interactions: 0
- Brand responses: 0
- Response rate: 0.00%
- Multi-turn rate: 0.00%
- Usable customer messages: 1,531,727
- Candidate score: 4.3751

## Selection methodology

Candidate brands were initially selected based on tweet volume. They were then compared using observable support-interaction characteristics, including response activity, multi-turn activity, message usability, and data volume. The final brand should be selected only after inspecting representative conversations.
