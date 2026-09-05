import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency
from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class PatternDiscovery:
    discovery_id: str
    problem_type: str
    segment_dict: Dict[str, str]
    segment_size: int
    baseline_size: int
    problem_rate: float
    baseline_rate: float
    relative_change: float
    affected_transactions: int
    chi2_stat: float
    p_value: float

def discover_patterns(df: pd.DataFrame) -> List[PatternDiscovery]:
    metrics = {
        'PAYMENT_FAILURE': 'payment_failure',
        'CHECKOUT_ABANDONMENT': 'checkout_abandoned',
        'REFUND_SPIKE': 'refund_requested_flag',
        'LOW_CONVERSION': 'low_conv',
        'CUSTOMER_PRICE_SENSITIVITY': 'price_sens'
    }
    
    df = df.copy()
    
    # Prepare custom metrics
    df['low_conv'] = 0.0
    mask_not_abandoned = (df.get('checkout_abandoned', 0) == 0) & (df.get('payment_failure', 0) == 0)
    if 'conversion_flag' in df.columns:
        df.loc[mask_not_abandoned, 'low_conv'] = (1 - df.loc[mask_not_abandoned, 'conversion_flag'])
    
    df['price_sens'] = 0.0
    if 'negotiation_started' in df.columns and 'negotiation_success' in df.columns:
        df['price_sens'] = (df['negotiation_started'].astype(int) & df['negotiation_success'])
        
    segments_defs = [
        ['device_type'], ['payment_method'], ['product_category'], ['location'], ['amount_bucket'],
        ['device_type', 'payment_method'], ['device_type', 'amount_bucket'], 
        ['payment_method', 'amount_bucket'], ['product_category', 'payment_method'], 
        ['merchant_id', 'product_category'],
        ['product_category', 'device_type'],
        ['product_category', 'amount_bucket'],
        ['location', 'payment_method'],
        ['location', 'device_type'],
        ['device_type', 'payment_method', 'is_late_night'], 
        ['device_type', 'payment_method', 'amount_bucket']
    ]
    
    discoveries = []
    discovery_counter = 1
    
    baseline_size = len(df)
    
    for segment_cols in segments_defs:
        # Check if cols exist
        if not all(c in df.columns for c in segment_cols):
            continue
            
        grouped = df.groupby(segment_cols)
        
        for name, group in grouped:
            if isinstance(name, tuple):
                segment_dict = dict(zip(segment_cols, name))
            else:
                segment_dict = {segment_cols[0]: name}
                
            segment_size = len(group)
            if segment_size < 30:
                continue
                
            for prob_type, target_col in metrics.items():
                if target_col not in df.columns:
                    continue
                    
                segment_rate = group[target_col].mean()
                baseline_rate = df[target_col].mean()
                
                if baseline_rate == 0:
                    continue
                    
                relative_change = segment_rate / baseline_rate
                abs_diff = segment_rate - baseline_rate
                
                if relative_change >= 2.0 and abs_diff >= 0.05:
                    # Chi-square test
                    segment_success = int(group[target_col].sum())
                    segment_fail = segment_size - segment_success
                    
                    baseline_success_ex = int(df[target_col].sum()) - segment_success
                    baseline_fail_ex = (baseline_size - segment_size) - baseline_success_ex
                    
                    # Ensure no negative counts
                    if segment_success < 0 or segment_fail < 0 or baseline_success_ex < 0 or baseline_fail_ex < 0:
                        continue
                        
                    contingency = [
                        [segment_success, segment_fail],
                        [baseline_success_ex, baseline_fail_ex]
                    ]
                    
                    try:
                        chi2, p, _, _ = chi2_contingency(contingency)
                    except ValueError:
                        continue
                        
                    if p < 0.05:
                        affected_transactions = segment_success
                        
                        discoveries.append(PatternDiscovery(
                            discovery_id=f"DISC-{discovery_counter:04d}",
                            problem_type=prob_type,
                            segment_dict=segment_dict,
                            segment_size=segment_size,
                            baseline_size=baseline_size,
                            problem_rate=segment_rate,
                            baseline_rate=baseline_rate,
                            relative_change=relative_change,
                            affected_transactions=affected_transactions,
                            chi2_stat=chi2,
                            p_value=p
                        ))
                        discovery_counter += 1
                        
    return discoveries
