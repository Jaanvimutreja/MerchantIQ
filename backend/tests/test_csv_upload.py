import io
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.ml.csv_normalizer import normalize_merchant_csv

client = TestClient(app)

SAMPLE_VALID_CSV = """total,status,gateway,platform,city
1200.50,completed,UPI,Android,Mumbai
2500.00,failed,NetBanking,Android,Delhi
300.00,paid,Card,iOS,Bangalore
4500.00,declined,NetBanking,Android,Delhi
150.00,completed,UPI,iOS,Hyderabad
"""

def test_normalize_merchant_csv_mappings():
    # Generate 35 rows so it meets the >= 30 row threshold
    rows = ["total,status,gateway,platform,city"]
    for i in range(40):
        amt = f"₹{(i + 1) * 100:.2f}"
        st = "paid" if i % 3 != 0 else "failed"
        gw = "NetBanking" if i % 2 == 0 else "UPI"
        dev = "Android" if i % 2 == 0 else "iOS"
        rows.append(f"{amt},{st},{gw},{dev},Mumbai")
    csv_text = "\n".join(rows)

    df_norm, summary, error_dict = normalize_merchant_csv(csv_text, "test.csv")
    assert error_dict is None
    assert df_norm is not None
    assert len(df_norm) == 40
    assert "amount" in df_norm.columns
    assert "payment_status" in df_norm.columns
    assert "payment_method" in df_norm.columns
    assert "device_type" in df_norm.columns
    assert df_norm["amount"].iloc[0] == 100.0
    assert df_norm["payment_status"].iloc[0] == "FAILED"  # 0 % 3 == 0 -> failed
    assert summary["mapped_columns"]["total"] == "amount"
    assert summary["mapped_columns"]["status"] == "payment_status"
    assert summary["mapped_columns"]["gateway"] == "payment_method"


def test_normalize_missing_required_fields():
    # CSV missing amount
    bad_csv = """order_id,status,gateway\nord_1,paid,UPI\n"""
    df_norm, summary, error_dict = normalize_merchant_csv(bad_csv)
    assert df_norm is None
    assert error_dict is not None
    assert error_dict["error_type"] == "INSUFFICIENT_DATA" or "MISSING_REQUIRED_FIELDS"


def test_normalize_insufficient_rows():
    bad_csv = """amount,payment_status,payment_method\n100,SUCCESS,UPI\n200,FAILED,Card\n"""
    df_norm, summary, error_dict = normalize_merchant_csv(bad_csv)
    assert df_norm is None
    assert error_dict["error_type"] == "INSUFFICIENT_DATA"
    assert "at least 30" in error_dict["message"]


def test_api_upload_csv_validation_failure():
    # Send CSV missing amount
    csv_data = "user_name,notes\nalice,hello\n"
    response = client.post(
        "/ai/analyze-csv",
        files={"file": ("test_missing.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert data["detail"]["error_type"] in ["INSUFFICIENT_DATA", "MISSING_REQUIRED_FIELDS"]


def test_api_upload_csv_success_and_reset():
    # Create valid CSV with 200 rows containing an obvious friction pattern
    # 50 Android transactions with 70% failure vs 150 iOS with 4% failure
    # Segment failure rate = 70%, Baseline failure rate ~ 20.5%, Relative change ~ 3.4x >= 2.0x
    rows = ["txn_amount,trans_status,pay_mode,client_type,geo"]
    for i in range(200):
        amt = 1500 + (i * 10)
        if i < 50:
            dev = "Android"
            gw = "NetBanking"
            st = "failed" if (i % 10 < 7) else "success" # 70% failure
        else:
            dev = "iOS"
            gw = "UPI"
            st = "failed" if (i % 25 == 0) else "success" # 4% failure
        rows.append(f"{amt},{st},{gw},{dev},Delhi")
    csv_content = "\n".join(rows).encode("utf-8")

    response = client.post(
        "/ai/analyze-csv",
        files={"file": ("merchant_orders.csv", io.BytesIO(csv_content), "text/csv")}
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert "summary" in res_data
    assert res_data["summary"]["is_custom"] is True
    assert res_data["summary"]["total_records"] == 200
    assert "discoveries" in res_data

    # Verify GET /ai/discoveries returns the updated discoveries
    disc_res = client.get("/ai/discoveries")
    assert disc_res.status_code == 200
    custom_discoveries = disc_res.json()
    assert len(custom_discoveries) > 0

    # Verify GET /ai/dataset-info matches discoveries and has 0 recovered revenue
    info_res = client.get("/ai/dataset-info")
    assert info_res.status_code == 200
    info_data = info_res.json()
    assert info_data["is_custom"] is True
    assert info_data["filename"] == "merchant_orders.csv"
    assert info_data["recovered_revenue"] == 0.0
    assert info_data["resolved_count"] == 0
    expected_risk = sum(d["estimated_revenue_at_risk"] for d in custom_discoveries)
    assert abs(info_data["revenue_at_risk"] - expected_risk) < 0.01

    # Fresh custom upload must have 0 resolutions and 0 investigations
    resolutions_res = client.get("/ai/resolutions")
    assert resolutions_res.status_code == 200
    assert resolutions_res.json() == []

    investigations_res = client.get("/ai/investigations")
    assert investigations_res.status_code == 200
    assert investigations_res.json() == []

    # Resolving a custom discovery works and is scoped to custom dataset
    target_d_id = custom_discoveries[0]["discovery_id"]
    resolve_res = client.post(f"/ai/resolve/{target_d_id}")
    assert resolve_res.status_code == 200
    res_entry = resolve_res.json()["resolution"]
    assert res_entry["discovery_id"] == target_d_id

    # Now GET /ai/resolutions returns exactly 1 resolution
    custom_res_list = client.get("/ai/resolutions").json()
    assert len(custom_res_list) == 1
    assert custom_res_list[0]["discovery_id"] == target_d_id

    # /ai/dataset-info now reflects the recovered amount
    updated_info = client.get("/ai/dataset-info").json()
    assert updated_info["resolved_count"] == 1
    assert updated_info["recovered_revenue"] == res_entry["recovered_amount"]

    # Reset to demo dataset
    reset_res = client.post("/ai/reset-demo")
    assert reset_res.status_code == 200
    reset_data = reset_res.json()
    assert reset_data["summary"]["is_custom"] is False
    assert reset_data["summary"]["total_records"] == 10000


def test_uploaded_csv_checkout_abandonment_discovery():
    """Verify that uploaded merchant CSV with checkout_status discovers CHECKOUT_ABANDONMENT."""
    # 50 Luxury transactions with 70% checkout abandonment vs 150 Books with 2% abandonment
    rows = ["order_id,amount,status,device,product_category,checkout_status"]
    for i in range(200):
        amt = 2500 + (i * 10)
        if i < 50:
            cat = "Luxury"
            dev = "Web"
            pay_st = "paid"
            chk_st = "abandoned" if (i % 10 < 7) else "completed"  # 70% abandonment
        else:
            cat = "Books"
            dev = "Mobile"
            pay_st = "paid"
            chk_st = "abandoned" if (i % 50 == 0) else "completed"  # 2% abandonment
        rows.append(f"ord_{i},{amt},{pay_st},{dev},{cat},{chk_st}")
    
    csv_content = "\n".join(rows).encode("utf-8")
    response = client.post(
        "/ai/analyze-csv",
        files={"file": ("merchant_checkout.csv", io.BytesIO(csv_content), "text/csv")}
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    
    discoveries = res_data["discoveries"]
    problem_types = {d["problem_type"] for d in discoveries}
    assert "CHECKOUT_ABANDONMENT" in problem_types
    
    # Find the luxury checkout abandonment discovery
    lux_discovery = next(
        (d for d in discoveries if d["problem_type"] == "CHECKOUT_ABANDONMENT" and d["segment"].get("product_category") == "Luxury"),
        None
    )
    assert lux_discovery is not None
    assert lux_discovery["affected_transactions"] >= 30
    assert lux_discovery["estimated_revenue_at_risk"] > 0
    assert lux_discovery["relative_change"] >= 2.0
    
    # Reset back to demo
    client.post("/ai/reset-demo")


def test_uploaded_csv_refund_spike_discovery():
    """Verify that uploaded merchant CSV with refund_status discovers REFUND_SPIKE."""
    # 50 Fashion transactions with 70% refund rate vs 150 Home transactions with 2% refund rate
    rows = ["invoice_id,order_value,payment_status,payment_mode,category,refund_status"]
    for i in range(200):
        amt = 1800 + (i * 10)
        if i < 50:
            cat = "Fashion"
            gw = "UPI"
            pay_st = "paid"
            ref_st = "refunded" if (i % 10 < 7) else "none"  # 70% refund rate
        else:
            cat = "Home"
            gw = "Card"
            pay_st = "paid"
            ref_st = "refunded" if (i % 50 == 0) else "none"  # 2% refund rate
        rows.append(f"inv_{i},{amt},{pay_st},{gw},{cat},{ref_st}")
    
    csv_content = "\n".join(rows).encode("utf-8")
    response = client.post(
        "/ai/analyze-csv",
        files={"file": ("merchant_refunds.csv", io.BytesIO(csv_content), "text/csv")}
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    
    discoveries = res_data["discoveries"]
    problem_types = {d["problem_type"] for d in discoveries}
    assert "REFUND_SPIKE" in problem_types
    
    # Find the fashion refund spike discovery
    fashion_discovery = next(
        (d for d in discoveries if d["problem_type"] == "REFUND_SPIKE" and d["segment"].get("product_category") == "Fashion"),
        None
    )
    assert fashion_discovery is not None
    assert fashion_discovery["affected_transactions"] >= 30
    assert fashion_discovery["estimated_revenue_at_risk"] > 0
    assert fashion_discovery["relative_change"] >= 2.0
    
    # Reset back to demo
    client.post("/ai/reset-demo")


def test_uploaded_csv_multi_pattern_all_three_types():
    """Verify that a single 500-row merchant CSV discovers PAYMENT_FAILURE, CHECKOUT_ABANDONMENT, and REFUND_SPIKE."""
    rows = ["id,value,state,mode,platform,vertical,checkout_status,refund_status"]
    for i in range(500):
        amt = 2000
        # Segment 1: Payment failure on NetBanking + Android in Electronics (60 rows, 45 failed = 75%)
        if i < 60:
            plat = "Android"
            gw = "NetBanking"
            vert = "Electronics"
            st = "failed" if i < 45 else "paid"
            chk_st = "completed"
            ref_st = "none"
        # Segment 2: Checkout abandonment on Luxury (60 rows, 40 abandoned = 66.7%)
        elif 60 <= i < 120:
            plat = "Web"
            gw = "Card"
            vert = "Luxury"
            st = "paid"
            chk_st = "abandoned" if i < 100 else "completed"
            ref_st = "none"
        # Segment 3: Refund spike on Fashion (60 rows, 40 refunded = 66.7%)
        elif 120 <= i < 180:
            plat = "Android"
            gw = "UPI"
            vert = "Fashion"
            st = "paid"
            chk_st = "completed"
            ref_st = "refunded" if i < 160 else "none"
        # Baseline: 320 rows with negligible friction
        else:
            plat = "Web"
            gw = "UPI"
            vert = "Home"
            st = "paid"
            chk_st = "completed"
            ref_st = "none"
        rows.append(f"txn_{i},{amt},{st},{gw},{plat},{vert},{chk_st},{ref_st}")
    
    csv_content = "\n".join(rows).encode("utf-8")
    response = client.post(
        "/ai/analyze-csv",
        files={"file": ("merchant_multi_500.csv", io.BytesIO(csv_content), "text/csv")}
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    
    discoveries = res_data["discoveries"]
    problem_types = {d["problem_type"] for d in discoveries}
    
    # Must detect all 3 problem types concurrently
    assert "PAYMENT_FAILURE" in problem_types
    assert "CHECKOUT_ABANDONMENT" in problem_types
    assert "REFUND_SPIKE" in problem_types
    
    # Verify dataset-info reflects the custom dataset and all 3 problem types
    info_res = client.get("/ai/dataset-info")
    assert info_res.status_code == 200
    info_data = info_res.json()
    assert info_data["is_custom"] is True
    assert info_data["filename"] == "merchant_multi_500.csv"
    assert info_data["total_records"] == 500
    assert info_data["problems_discovered"] == len(discoveries)
    
    # Reset back to demo
    client.post("/ai/reset-demo")

