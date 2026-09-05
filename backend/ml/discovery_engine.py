import pandas as pd
import numpy as np
from typing import List, Dict, Any
from pathlib import Path
import math

try:
    # When run from project root (tests / scripts)
    import backend.ml.feature_engineering as fe
    import backend.ml.anomaly_detector as ad
    import backend.ml.pattern_discovery as pd_mod
    import backend.ml.impact_calculator as ic
except ImportError:
    # When run from backend/ (uvicorn, normal startup)
    import ml.feature_engineering as fe
    import ml.anomaly_detector as ad
    import ml.pattern_discovery as pd_mod
    import ml.impact_calculator as ic

class DiscoveryEngine:
    def run(self, csv_path: str) -> List[Dict[str, Any]]:
        # 1. Feature Engineering
        df = fe.load_and_engineer(csv_path)
        
        # 2. Anomaly Detection
        df = ad.detect_anomalies(df)
        
        # 3. Pattern Discovery
        raw_patterns = pd_mod.discover_patterns(df)
        
        discoveries = []
        for pattern in raw_patterns:
            # 4. Calculate Impact
            impact = ic.calculate_impact(df, pattern)
            
            # 5. Score Discovery
            mask = pd.Series(True, index=df.index)
            for k, v in pattern.segment_dict.items():
                if k in df.columns:
                    mask = mask & (df[k] == v)
            segment_df = df[mask]
            
            if len(segment_df) == 0:
                continue
                
            anomaly_strength = segment_df['is_anomaly'].mean()
            
            affected_vol = max(pattern.affected_transactions, 1)
            affected_volume_factor = math.log10(affected_vol) / math.log10(10000)
            
            rev_impact = max(impact, 1)
            revenue_impact_factor = math.log10(rev_impact) / math.log10(10000000)
            
            confidence_factor = 1.0 - pattern.p_value
            
            rel_change_norm = min(pattern.relative_change / 10.0, 1.0)
            
            raw_score = (
                anomaly_strength * 0.25 + 
                rel_change_norm * 0.30 + 
                affected_volume_factor * 0.20 + 
                revenue_impact_factor * 0.15 + 
                confidence_factor * 0.10
            )
            
            priority_score = round(raw_score * 100, 1)
            
            # 6. Assign severity
            if priority_score >= 60:
                severity = 'HIGH'
            elif priority_score >= 35:
                severity = 'MEDIUM'
            else:
                severity = 'LOW'
                
            # 7. Generate title
            pri_seg_val = " & ".join([f"{k}={v}" for k, v in pattern.segment_dict.items()])
            title = f"{pattern.problem_type.replace('_', ' ').title()} in {pri_seg_val}"
            
            # 8. Generate evidence list
            evidence = [
                f"Segment rate: {pattern.problem_rate:.1%} vs Global baseline: {pattern.baseline_rate:.1%}",
                f"Relative change: {pattern.relative_change:.2f}x (p-value={pattern.p_value:.4f})",
                f"Affected transactions: {pattern.affected_transactions} out of {pattern.segment_size} in segment",
                f"Anomaly density in segment: {anomaly_strength:.1%}"
            ]
            
            discoveries.append({
                'discovery_id': pattern.discovery_id,
                'problem_type': pattern.problem_type,
                'title': title,
                'segment': pattern.segment_dict,
                'severity': severity,
                'priority_score': priority_score,
                'affected_transactions': pattern.affected_transactions,
                'problem_rate': pattern.problem_rate,
                'baseline_rate': pattern.baseline_rate,
                'relative_change': pattern.relative_change,
                'estimated_revenue_at_risk': impact,
                'evidence': evidence,
                'detection_method': ['IsolationForest', 'Chi-Square Proportions', 'Segment Aggregation']
            })
            
        # 9. Deduplicate
        discoveries.sort(key=lambda x: x['priority_score'], reverse=True)
        deduped = []
        seen = []
        for d in discoveries:
            is_dup = False
            for s in seen:
                if d['problem_type'] == s['problem_type']:
                    # Check overlap in segment dict
                    shared_keys = set(d['segment'].keys()).intersection(set(s['segment'].keys()))
                    if any(d['segment'][k] == s['segment'][k] for k in shared_keys):
                        is_dup = True
                        break
            if not is_dup:
                deduped.append(d)
                seen.append(d)
                
        # 10. Return top 20
        return deduped[:20]
