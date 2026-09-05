"""
Synthetic Merchant Event Dataset Generator for BargainAI2
Generates 10,000 realistic merchant transaction and customer behavior records
with embedded latent behavioural patterns (without explicit problem labels).

Patterns embedded:
- Pattern A (Payment Friction): Specific device + payment method + night time window has elevated failure rates.
- Pattern B (Checkout Friction / Funnel Dropoff): High-value carts with complex payment methods show elevated abandonment & long checkout duration.
- Pattern C (Price Sensitivity / Bargain-Seeking): High repeat bargaining behavior that readily converts when small discounts or counter-offers are accepted.
- Pattern D (Post-Purchase Dissatisfaction): Certain category/merchant combinations experience elevated refund rates due to fit/expectation issues.
"""

import csv
import math
import os
import random
from datetime import datetime, timedelta

# Set fixed seed for strict reproducibility
SEED = 42
random.seed(SEED)

NUM_RECORDS = 10000

# Merchants pool (IDs, categories, tier)
MERCHANTS = [
    {"merchant_id": "mer_elec_01", "name": "Apex Electronics", "category": "Consumer Electronics", "avg_order_value": 4500},
    {"merchant_id": "mer_fash_02", "name": "Urban Vogue Apparel", "category": "Fashion & Apparel", "avg_order_value": 1800},
    {"merchant_id": "mer_home_03", "name": "CozyHaven Living", "category": "Home & Kitchen", "avg_order_value": 3200},
    {"merchant_id": "mer_gadg_04", "name": "GizmoPulse Accessories", "category": "Mobile & Accessories", "avg_order_value": 1200},
    {"merchant_id": "mer_fitn_05", "name": "IronPeak Activewear", "category": "Fitness & Sports", "avg_order_value": 2400},
    {"merchant_id": "mer_lux_06",  "name": "Aura Luxury Timepieces", "category": "Luxury & Watches", "avg_order_value": 14000},
]

# Customer cohorts to simulate repeated customer behaviour
# Cohort types:
# 1. 'bargain_hunter': high affinity for negotiations, price sensitive (Pattern C)
# 2. 'impulse_buyer': quick checkout, mobile-first, standard behavior
# 3. 'cautious_shopper': long checkout, susceptible to abandonment (Pattern B)
# 4. 'regular': normal e-commerce shopper
NUM_CUSTOMERS = 1800
CUSTOMERS = []
for i in range(1, NUM_CUSTOMERS + 1):
    c_id = f"cust_{i:04d}"
    r = random.random()
    if r < 0.22:
        persona = "bargain_hunter"
    elif r < 0.45:
        persona = "cautious_shopper"
    elif r < 0.70:
        persona = "impulse_buyer"
    else:
        persona = "regular"
    CUSTOMERS.append({
        "customer_id": c_id,
        "persona": persona,
        "primary_device": random.choice(["Android", "iOS", "Windows", "MacOS"]),
        "location": random.choices(
            ["Mumbai", "Bengaluru", "Delhi NCR", "Hyderabad", "Pune", "Chennai", "Kolkata", "Ahmedabad", "Jaipur", "Lucknow"],
            weights=[22, 20, 18, 10, 8, 7, 5, 4, 3, 3]
        )[0]
    })

PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Net Banking", "Wallet", "EMI"]
PAYMENT_METHOD_WEIGHTS = [0.55, 0.20, 0.12, 0.05, 0.05, 0.03]

DEVICE_TYPES = ["Android", "iOS", "Windows", "MacOS"]
DEVICE_WEIGHTS = [0.52, 0.24, 0.18, 0.06]

FAILURE_REASONS_GATEWAY = [
    "GATEWAY_TIMEOUT",
    "BANK_SERVER_DOWN",
    "INSUFFICIENT_FUNDS",
    "AUTHENTICATION_FAILED",
    "USER_DROPPED_AT_OTP",
    "NETWORK_ERROR",
]

def generate_events():
    events = []
    
    # Base timestamp window: Last 45 days up to now
    end_time = datetime(2026, 9, 5, 11, 0, 0)
    start_time = end_time - timedelta(days=45)
    total_seconds = int((end_time - start_time).total_seconds())

    # Pre-sort random timestamps so events are chronologically ordered
    event_timestamps = sorted([
        start_time + timedelta(seconds=random.randint(0, total_seconds))
        for _ in range(NUM_RECORDS)
    ])

    for idx, event_time in enumerate(event_timestamps, 1):
        event_id = f"evt_{idx:06d}"
        order_id = f"ord_{100000 + idx}"
        
        # Pick customer (with heavy reuse to show repeat behavior)
        # Power law / Zipf distribution on customer selection
        cust_idx = int((random.random() ** 1.8) * NUM_CUSTOMERS)
        cust_idx = min(cust_idx, NUM_CUSTOMERS - 1)
        customer = CUSTOMERS[cust_idx]
        customer_id = customer["customer_id"]
        persona = customer["persona"]
        
        # Device: mostly customer's primary, occasionally different
        if random.random() < 0.85:
            device_type = customer["primary_device"]
        else:
            device_type = random.choices(DEVICE_TYPES, weights=DEVICE_WEIGHTS)[0]
            
        location = customer["location"]
        
        # Pick merchant
        merchant = random.choice(MERCHANTS)
        merchant_id = merchant["merchant_id"]
        product_category = merchant["category"]
        
        # Payment method
        payment_method = random.choices(PAYMENT_METHODS, weights=PAYMENT_METHOD_WEIGHTS)[0]
        
        # Transaction Amount: Log-normal distribution around merchant's avg order value
        mu = math.log(merchant["avg_order_value"])
        sigma = 0.45
        raw_amount = math.exp(random.gauss(mu, sigma))
        amount = round(max(150.0, min(raw_amount, 95000.0)), 2)
        
        hour = event_time.hour
        is_night_window = (hour >= 23 or hour <= 4)
        
        # Default baseline metrics
        checkout_duration = max(12, int(random.gauss(95, 30)))  # in seconds
        retry_count = 0
        cart_abandoned = False
        negotiation_started = False
        negotiation_rounds = 0
        discount_requested = 0.0
        discount_given = 0.0
        payment_status = "SUCCESS"
        failure_reason = ""
        refund_requested = False
        refund_status = "NONE"
        final_order_status = "COMPLETED"

        # ── PATTERN A: Device + Payment Method + Time Window Friction ──
        # Latent condition: Android + Net Banking or Debit Card during late night (23:00 - 04:00)
        # Reason: Specific banking gateway batch settlement issues on mobile web view
        is_pattern_a_trigger = (
            device_type == "Android"
            and payment_method in ["Net Banking", "Debit Card"]
            and is_night_window
        )
        
        # ── PATTERN B: High Value Checkout Friction / Cart Abandonment ──
        # Latent condition: High value items (> ₹6,000) or Cautious Shopper persona on EMI/Credit Card
        is_pattern_b_trigger = (
            (amount > 6500 or persona == "cautious_shopper")
            and payment_method in ["EMI", "Credit Card", "Net Banking"]
        )

        # ── PATTERN C: Negotiation / Bargain-Seeking Behavior ──
        # Latent condition: Persona is 'bargain_hunter' or Consumer Electronics / Fitness category
        is_pattern_c_trigger = (
            persona == "bargain_hunter"
            or (product_category in ["Consumer Electronics", "Fitness & Sports"] and random.random() < 0.28)
        )

        # ── PATTERN D: Elevated Return / Refund in Specific Segment ──
        # Latent condition: Urban Vogue Apparel (Fashion) + Tier 1/2 Cities (Fit/Size mismatch)
        is_pattern_d_trigger = (
            merchant_id == "mer_fash_02"
            and amount > 2000
        )

        # --- Resolve Negotiation Module ---
        if is_pattern_c_trigger:
            negotiation_started = True
            negotiation_rounds = random.choices([1, 2, 3, 4], weights=[0.45, 0.35, 0.15, 0.05])[0]
            discount_pct = random.uniform(0.08, 0.25)
            discount_requested = round(amount * discount_pct, 2)
            
            # Merchant accepts modest discounts (8% - 15%), rejects steeper ones unless clear inventory
            if discount_pct <= 0.15:
                discount_given = discount_requested
            else:
                # Counter-offer acceptance
                discount_given = round(amount * random.uniform(0.06, 0.12), 2)
            checkout_duration += negotiation_rounds * 45
        else:
            if random.random() < 0.04:  # baseline small negotiation
                negotiation_started = True
                negotiation_rounds = 1
                discount_requested = round(amount * 0.05, 2)
                discount_given = discount_requested if random.random() < 0.5 else 0.0
                checkout_duration += 30

        # --- Resolve Cart Abandonment (Pattern B) ---
        if is_pattern_b_trigger and random.random() < 0.42:
            cart_abandoned = True
            checkout_duration = max(180, int(random.gauss(340, 90)))
            payment_status = "ABANDONED"
            failure_reason = "CHECKOUT_TIMEOUT_USER_ABANDONED"
            final_order_status = "ABANDONED"
        elif random.random() < 0.06:  # Baseline cart abandonment
            cart_abandoned = True
            checkout_duration = max(120, int(random.gauss(220, 60)))
            payment_status = "ABANDONED"
            failure_reason = "USER_DROPPED_AT_OTP"
            final_order_status = "ABANDONED"

        # --- Resolve Payment Execution (if not abandoned) ---
        if not cart_abandoned:
            if is_pattern_a_trigger:
                # Unusually high failure rate (58% vs baseline ~6%)
                if random.random() < 0.58:
                    payment_status = "FAILED"
                    retry_count = random.choices([1, 2, 3], weights=[0.5, 0.35, 0.15])[0]
                    failure_reason = random.choice(["GATEWAY_TIMEOUT", "BANK_SERVER_DOWN", "NETWORK_ERROR"])
                    final_order_status = "FAILED"
                    checkout_duration += retry_count * 35
                else:
                    payment_status = "SUCCESS"
                    retry_count = random.choice([0, 1])
                    final_order_status = "COMPLETED"
            else:
                # Standard baseline payment failure (~6.5%)
                if random.random() < 0.065:
                    payment_status = "FAILED"
                    retry_count = random.choices([0, 1, 2], weights=[0.6, 0.3, 0.1])[0]
                    failure_reason = random.choice(FAILURE_REASONS_GATEWAY)
                    final_order_status = "FAILED"
                    checkout_duration += retry_count * 25
                else:
                    payment_status = "SUCCESS"
                    retry_count = 0
                    final_order_status = "COMPLETED"

        # --- Resolve Refunds (Pattern D) ---
        if payment_status == "SUCCESS":
            if is_pattern_d_trigger and random.random() < 0.31:
                # 31% refund request in high-value apparel (vs baseline ~4%)
                refund_requested = True
                # 88% approved, 12% rejected
                refund_status = "PROCESSED" if random.random() < 0.88 else "REJECTED"
                final_order_status = "REFUNDED" if refund_status == "PROCESSED" else "COMPLETED"
            elif random.random() < 0.038:  # Baseline refund rate
                refund_requested = True
                refund_status = "PROCESSED" if random.random() < 0.82 else "REJECTED"
                final_order_status = "REFUNDED" if refund_status == "PROCESSED" else "COMPLETED"

        events.append({
            "event_id": event_id,
            "merchant_id": merchant_id,
            "customer_id": customer_id,
            "order_id": order_id,
            "timestamp": event_time.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": f"{amount:.2f}",
            "product_category": product_category,
            "payment_method": payment_method,
            "device_type": device_type,
            "location": location,
            "payment_status": payment_status,
            "failure_reason": failure_reason,
            "retry_count": retry_count,
            "checkout_duration": checkout_duration,
            "cart_abandoned": cart_abandoned,
            "refund_requested": refund_requested,
            "refund_status": refund_status,
            "discount_requested": f"{discount_requested:.2f}",
            "discount_given": f"{discount_given:.2f}",
            "negotiation_started": negotiation_started,
            "negotiation_rounds": negotiation_rounds,
            "final_order_status": final_order_status,
        })

    return events


def save_to_csv(events, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fieldnames = [
        "event_id",
        "merchant_id",
        "customer_id",
        "order_id",
        "timestamp",
        "amount",
        "product_category",
        "payment_method",
        "device_type",
        "location",
        "payment_status",
        "failure_reason",
        "retry_count",
        "checkout_duration",
        "cart_abandoned",
        "refund_requested",
        "refund_status",
        "discount_requested",
        "discount_given",
        "negotiation_started",
        "negotiation_rounds",
        "final_order_status",
    ]
    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(events)
    print(f"Successfully generated {len(events)} events saved to: {output_path}")


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_csv = os.path.join(current_dir, "merchant_events.csv")
    print(f"Generating {NUM_RECORDS} synthetic merchant events (seed={SEED})...")
    data = generate_events()
    save_to_csv(data, output_csv)
