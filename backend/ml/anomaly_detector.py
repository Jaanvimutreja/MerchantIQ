import pandas as pd
from sklearn.ensemble import IsolationForest

def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    features = [
        'amount', 'checkout_duration', 'retry_count', 'negotiation_rounds',
        'discount_requested', 'discount_given', 'hour', 'day_of_week',
        'payment_failure', 'checkout_abandoned', 'refund_requested_flag',
        'negotiation_success', 'conversion_flag'
    ]
    
    # Filter features that exist
    features = [f for f in features if f in df.columns]
    
    if not features:
        df['anomaly_score'] = 0.0
        df['is_anomaly'] = False
        return df
        
    # Fill any NaNs
    X = df[features].fillna(0)
    
    iso = IsolationForest(contamination=0.08, random_state=42)
    iso.fit(X)
    
    df['anomaly_score'] = iso.decision_function(X)
    df['is_anomaly'] = iso.predict(X) == -1
    
    return df
