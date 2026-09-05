# BargainAI2 Discovery Engine

This module implements a genuine machine learning and statistical problem discovery engine for e-commerce transactions. 
Unlike simple LLM wrappers, it relies on rigorous data science techniques to surface actionable insights.

## Pipeline Architecture
1. **Feature Engineering**: Derives new features from raw event data (e.g., `is_late_night`, `amount_bucket`).
2. **Anomaly Detection**: Uses `IsolationForest` to compute anomaly scores for transactions across all engineered features.
3. **Pattern Discovery**: Enumerates multi-dimensional segments and calculates business metrics (e.g., checkout abandonment rate, refund spike). Uses Chi-square tests to ensure statistical significance ($p < 0.05$) of changes vs. global baseline.
4. **Impact Calculator**: Estimates `estimated_revenue_at_risk` based on problem type and affected transaction volume.
5. **Scoring & Prioritization**: Computes a robust `priority_score` using normalized components of relative rate changes, volume factors, revenue risk, and anomaly density.
6. **Deduplication**: Removes overlapping segments discovering similar problems to surface only the most salient insights.

## Assumptions for Revenue Impact
- **PAYMENT_FAILURE**: 65% of failed payments are recoverable via better gateway routing.
- **CHECKOUT_ABANDONMENT**: 40% cart recovery potential.
- **REFUND_SPIKE**: Full amount of requested refunds is considered at risk.
- **LOW_CONVERSION**: 30% of missed conversions in the segment might be recaptured.
- **CUSTOMER_PRICE_SENSITIVITY**: Full sum of negotiated discounts given away.

## Limitations
- Static anomaly threshold (`contamination=0.08`).
- Segment evaluation is greedy and may miss higher-order interactions beyond 3 dimensions.
- Assumes linear relationship for revenue impact recovery which might vary by product category.
