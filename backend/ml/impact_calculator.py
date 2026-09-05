import pandas as pd
from typing import Any

def calculate_impact(df: pd.DataFrame, pattern: Any) -> float:
    # Filter dataframe by segment_dict
    mask = pd.Series(True, index=df.index)
    for k, v in pattern.segment_dict.items():
        if k in df.columns:
            mask = mask & (df[k] == v)
            
    segment_df = df[mask]
    
    if pattern.problem_type == 'PAYMENT_FAILURE':
        failed = segment_df[segment_df['payment_failure'] == 1]
        return float(failed['amount'].sum() * 0.65)
        
    elif pattern.problem_type == 'CHECKOUT_ABANDONMENT':
        abandoned = segment_df[segment_df['checkout_abandoned'] == 1]
        return float(abandoned['amount'].sum() * 0.40)
        
    elif pattern.problem_type == 'REFUND_SPIKE':
        refunds = segment_df[segment_df['refund_requested_flag'] == 1]
        return float(refunds['amount'].sum())
        
    elif pattern.problem_type == 'LOW_CONVERSION':
        avg_amount = segment_df['amount'].mean()
        if pd.isna(avg_amount):
            avg_amount = 0
        return float(avg_amount * pattern.affected_transactions * 0.30)
        
    elif pattern.problem_type == 'CUSTOMER_PRICE_SENSITIVITY':
        if 'discount_given' in segment_df.columns:
            # sum of discount_given for successful negotiations
            neg_success = segment_df[segment_df['negotiation_success'] == 1]
            return float(neg_success['discount_given'].astype(float).sum())
            
    return 0.0
