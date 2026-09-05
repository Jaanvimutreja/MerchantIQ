import pandas as pd
import numpy as np


def _parse_bool_signal(series: pd.Series, positive_keywords: set) -> pd.Series:
    """Safely parse boolean or string status column into 0/1 binary integer series."""
    if series.dtype == bool:
        return series.astype(int)
    if pd.api.types.is_numeric_dtype(series):
        return (series > 0).astype(int)
    s = series.fillna("").astype(str).str.strip().str.lower()
    truthy = {"true", "1", "yes", "y", "t"}.union({k.lower() for k in positive_keywords})
    return s.isin(truthy).astype(int)


def load_and_engineer(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    
    # Ensure amount is float
    if 'amount' in df.columns:
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0.0).astype(float)
    
    if 'timestamp' in df.columns:
        dt = pd.to_datetime(df['timestamp'], errors='coerce')
        df['hour'] = dt.dt.hour.fillna(0).astype(int)
        df['day_of_week'] = dt.dt.dayofweek.fillna(0).astype(int)
        df['is_late_night'] = ((df['hour'] >= 23) | (df['hour'] <= 4)).astype(int)
    else:
        df['hour'] = 0
        df['day_of_week'] = 0
        df['is_late_night'] = 0
        
    if 'amount' in df.columns:
        df['amount_bucket'] = pd.cut(df['amount'], bins=[-np.inf, 500, 2000, 5000, 15000, np.inf], 
                                     labels=['<500', '500-2K', '2K-5K', '5K-15K', '>15K']).astype(str)
        df['high_value_transaction'] = (df['amount'] > 6500).astype(int)
        
    if 'payment_status' in df.columns:
        df['payment_failure'] = (df['payment_status'].astype(str).str.upper() == 'FAILED').astype(int)
    else:
        df['payment_failure'] = 0
        
    # Checkout abandonment signal
    abandoned_signal = pd.Series(0, index=df.index)
    if 'cart_abandoned' in df.columns:
        abandoned_signal = abandoned_signal | _parse_bool_signal(
            df['cart_abandoned'],
            {'abandoned', 'dropped', 'incomplete', 'cart_abandoned', 'checkout_abandoned', 'bounced', 'exit', 'exited', 'cancelled', 'canceled'}
        )
    if 'checkout_status' in df.columns:
        abandoned_signal = abandoned_signal | _parse_bool_signal(
            df['checkout_status'],
            {'abandoned', 'dropped', 'incomplete', 'cart_abandoned', 'checkout_abandoned', 'bounced', 'exit', 'exited'}
        )
    if 'cart_status' in df.columns:
        abandoned_signal = abandoned_signal | _parse_bool_signal(
            df['cart_status'],
            {'abandoned', 'dropped', 'incomplete', 'cart_abandoned'}
        )
    if 'order_status' in df.columns:
        abandoned_signal = abandoned_signal | _parse_bool_signal(
            df['order_status'],
            {'abandoned', 'dropped', 'incomplete'}
        )
    df['checkout_abandoned'] = abandoned_signal.astype(int)
        
    # Refund requested signal
    refund_signal = pd.Series(0, index=df.index)
    if 'refund_requested' in df.columns:
        refund_signal = refund_signal | _parse_bool_signal(
            df['refund_requested'],
            {'refunded', 'requested', 'refund_requested', 'returned', 'chargeback', 'disputed', 'partial_refund', 'refund', 'reversal'}
        )
    if 'refund_status' in df.columns:
        refund_signal = refund_signal | _parse_bool_signal(
            df['refund_status'],
            {'refunded', 'requested', 'refund_requested', 'returned', 'chargeback', 'disputed', 'partial_refund', 'refund', 'reversal'}
        )
    if 'order_status' in df.columns:
        refund_signal = refund_signal | _parse_bool_signal(
            df['order_status'],
            {'refunded', 'returned', 'chargeback', 'disputed'}
        )
    df['refund_requested_flag'] = refund_signal.astype(int)
        
    if 'negotiation_started' in df.columns and 'discount_given' in df.columns:
        neg_started = _parse_bool_signal(df['negotiation_started'], set())
        disc_given = pd.to_numeric(df['discount_given'], errors='coerce').fillna(0.0)
        df['negotiation_success'] = (neg_started.astype(bool) & (disc_given > 0)).astype(int)
    else:
        df['negotiation_success'] = 0
        
    if 'final_order_status' in df.columns:
        s_final = df['final_order_status'].fillna("").astype(str).str.strip().str.upper()
        df['conversion_flag'] = s_final.isin({'COMPLETED', 'SUCCESS', 'PAID', 'DELIVERED', 'CAPTURED'}).astype(int)
    elif 'order_status' in df.columns:
        s_order = df['order_status'].fillna("").astype(str).str.strip().str.upper()
        df['conversion_flag'] = s_order.isin({'COMPLETED', 'SUCCESS', 'PAID', 'DELIVERED', 'CAPTURED'}).astype(int)
    else:
        df['conversion_flag'] = (df.get('payment_status') == 'SUCCESS').astype(int)
        
    if 'retry_count' in df.columns:
        retries = pd.to_numeric(df['retry_count'], errors='coerce').fillna(0).astype(int)
        df['retry_bucket'] = np.where(retries == 0, '0', 
                                      np.where(retries == 1, '1', '2+'))
    else:
        df['retry_bucket'] = '0'
        
    return df

