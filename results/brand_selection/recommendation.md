# Brand Selection Recommendation

Candidate brands are ranked using observable interaction signals from the Customer Support on Twitter dataset.

**Important:** the dataset does not provide an explicit resolution label. These metrics therefore represent observable interaction proxies rather than ground-truth resolution rates.

## Ranking signals

- Support reply volume: 40%
- Unique customers: 25%
- Observable reply rate: 20%
- Total support tweet volume: 15%

## Candidate ranking

| brand           |   tweet_count |   support_replies |   unique_customers |   reply_rate |   candidate_score |
|:----------------|--------------:|------------------:|-------------------:|-------------:|------------------:|
| AmazonHelp      |        169840 |            169287 |              71048 |     0.996744 |          0.964661 |
| AppleSupport    |        106860 |            106719 |              76365 |     0.998681 |          0.780526 |
| Uber_Support    |         56270 |             56261 |              38299 |     0.99984  |          0.486196 |
| SpotifyCares    |         43265 |             43243 |              27793 |     0.999492 |          0.404539 |
| Delta           |         42253 |             42197 |              22329 |     0.998675 |          0.378128 |
| comcastcares    |         33031 |             33007 |              21823 |     0.999273 |          0.348404 |
| TMobileHelp     |         34317 |             34287 |              19942 |     0.999126 |          0.345575 |
| AmericanAir     |         36764 |             36598 |              21686 |     0.995485 |          0.34014  |
| Tesco           |         38573 |             38501 |              15593 |     0.998133 |          0.339859 |
| SouthwestAir    |         28977 |             28889 |              19712 |     0.996963 |          0.315074 |
| British_Airways |         29361 |             29315 |              14212 |     0.998433 |          0.305596 |
| Ask_Spectrum    |         25860 |             25807 |              17213 |     0.997951 |          0.301344 |
| sprintcare      |         22381 |             22335 |              12895 |     0.997945 |          0.274868 |
| hulu_support    |         21872 |             21783 |              13461 |     0.995931 |          0.264274 |
| UPSHelp         |         17817 |             17772 |              14614 |     0.997474 |          0.262744 |

## Top 3 candidates

### AmazonHelp

- Support tweets: 169,840
- Support replies: 169,287
- Unique customers: 71,048
- Observable reply rate: 99.67%
- Candidate score: 0.965

### AppleSupport

- Support tweets: 106,860
- Support replies: 106,719
- Unique customers: 76,365
- Observable reply rate: 99.87%
- Candidate score: 0.781

### Uber_Support

- Support tweets: 56,270
- Support replies: 56,261
- Unique customers: 38,299
- Observable reply rate: 99.98%
- Candidate score: 0.486

