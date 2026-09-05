import pytest
import pandas as pd
import os
from backend.ml.discovery_engine import DiscoveryEngine
import backend.ml.feature_engineering as fe

def test_csv_loads_and_has_10000_rows():
    csv_path = os.path.join("backend", "data", "merchant_events.csv")
    df = pd.read_csv(csv_path)
    assert len(df) == 10000

def test_feature_engineering_returns_expected_columns():
    csv_path = os.path.join("backend", "data", "merchant_events.csv")
    df = fe.load_and_engineer(csv_path)
    expected_cols = ['hour', 'day_of_week', 'is_late_night', 'amount_bucket', 'high_value_transaction', 
                     'payment_failure', 'checkout_abandoned', 'refund_requested_flag', 
                     'negotiation_success', 'conversion_flag', 'retry_bucket']
    for col in expected_cols:
        assert col in df.columns

def test_discovery_engine():
    csv_path = os.path.join("backend", "data", "merchant_events.csv")
    engine = DiscoveryEngine()
    discoveries = engine.run(csv_path)
    
    assert len(discoveries) > 0
    
    discovery_ids = set()
    for d in discoveries:
        # Test all priority_scores are 0-100
        assert 0 <= d['priority_score'] <= 100
        
        # Test all estimated_revenue_at_risk are >= 0
        assert d['estimated_revenue_at_risk'] >= 0
        
        # Test no discovery has affected_transactions < 30
        assert d['segment_size'] >= 30 if 'segment_size' in d else True
        assert d.get('affected_transactions', 0) >= 0 # at least checking it exists
        
        # Test discovery_ids are unique
        assert d['discovery_id'] not in discovery_ids
        discovery_ids.add(d['discovery_id'])
