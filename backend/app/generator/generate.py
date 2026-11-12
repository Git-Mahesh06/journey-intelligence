
import argparse
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import insert, text

from app.db.database import engine
from app.models.entities import (
    Customer, SessionRecord, JourneyEvent, Page, Product,
    Cart, Order, SupportTicket, Experiment, JourneyOutcome,
    IdentityLink, GroundTruth,
    cart_items, order_items, session_experiments,
)


SEED = 20261022
EVENTS_PER_SESSION = 20
BASE_TIME = datetime(2026, 10, 1, tzinfo=timezone.utc)

CHANNELS = ["web", "mobile_app"]
PRODUCT_COUNT = 100
CUSTOMER_COUNT = 5000
BATCH_SIZE = 500


def generate_master_data(conn, rng):
    print("Generating master data...")

    customers = []
    for i in range(1, CUSTOMER_COUNT + 1):
        customers.append({
            "customer_id": f"CUS-{i:06d}",
            "email": f"customer{i}@example.test",
            "name": f"Customer {i}",
            "consent_status": rng.choice(
                ["granted", "denied", "unknown"]
            ),
        })

    products = []
    for i in range(1, PRODUCT_COUNT + 1):
        products.append({
            "product_id": f"PRD-{i:06d}",
            "product_name": f"Product {i}",
            "category": rng.choice(
                ["Electronics", "Fashion", "Home", "Accessories"]
            ),
            "price": round(rng.uniform(500, 80000), 2),
            "status": "active",
        })

    pages = []
    for i in range(1, 31):
        pages.append({
            "page_id": f"PAG-{i:04d}",
            "page_name": f"Page {i}",
            "page_url": f"https://example.test/page/{i}",
            "page_type": rng.choice(
                ["home", "product", "search", "cart", "checkout"]
            ),
            "product_id": f"PRD-{rng.randint(1, PRODUCT_COUNT):06d}",
        })

    experiments = []
    for i in range(1, 6):
        experiments.append({
            "experiment_id": f"EXP-2026-{i:06d}",
            "experiment_name": f"Checkout Experiment {i}",
            "status": "active",
            "start_date": BASE_TIME.date(),
        })

    conn.execute(insert(Customer), customers)
    conn.execute(insert(Product), products)
    conn.execute(insert(Page), pages)
    conn.execute(insert(Experiment), experiments)

    print("Master data created.")


def choose_outcome(rng, scenario):
    if scenario == "duplicate_conversion":
        return "converted"

    value = rng.random()

    if value < 0.25:
        return "converted"
    elif value < 0.65:
        return "abandoned"
    elif value < 0.80:
        return "support_contact"
    return "browse_only"


def build_event_types(outcome, scenario, rng):
    events = [
        "session_started",
        "page_view",
        "product_view",
        "search",
        "product_view",
    ]

    if outcome != "browse_only":
        events.extend(["add_to_cart", "cart_view"])

    if outcome in ["converted", "abandoned", "support_contact"]:
        events.extend(["checkout_started", "payment_initiated"])

    if outcome == "support_contact":
        events.append("payment_failed")

    fillers = [
        "page_view",
        "product_view",
        "scroll",
        "filter_applied",
        "app_open",
    ]

    terminal = {
        "converted": "payment_success",
        "abandoned": "session_abandoned",
        "support_contact": "support_contact",
        "browse_only": "session_ended",
    }[outcome]

    target_size = EVENTS_PER_SESSION - 1

    if scenario == "duplicate_conversion":
        target_size = EVENTS_PER_SESSION - 2

    while len(events) < target_size:
        events.append(rng.choice(fillers))

    events.append(terminal)

    if scenario == "duplicate_conversion":
        events.append("payment_success")

    return events


def scenario_for(session_number):
    remainder = session_number % 100

    if remainder == 0:
        return "out_of_order"

    if remainder == 1:
        return "incorrect_identity_merge"

    if remainder == 2:
        return "duplicate_conversion"

    if remainder == 3:
        return "bot_traffic"

    return None



def generate_batch(conn, start, end, rng):

    # --------------------------------------------------
    # 1. Load customer consent information
    # --------------------------------------------------
    consent_map = dict(
        conn.execute(
            text("SELECT customer_id, consent_status FROM customers")
        ).all()
    )

    # Identify customers who denied consent
    denied_customer_ids = [
        cid
        for cid, status in consent_map.items()
        if status == "denied"
    ]

    if not denied_customer_ids:
        raise ValueError(
            "No customers with denied consent found. "
            "Cannot generate identity-merge exception."
        )

    # --------------------------------------------------
    # 2. Initialize batch collections
    # --------------------------------------------------
    sessions = []
    events = []
    carts = []
    orders = []
    tickets = []
    outcomes = []

    cart_item_rows = []
    order_item_rows = []
    experiment_rows = []
    identity_rows = []
    truth_rows = []

    # --------------------------------------------------
    # 3. Generate each session
    # --------------------------------------------------
    for number in range(start, end):

        session_id = f"SES-2026-{number:06d}"

        # Determine injected exception scenario
        scenario = scenario_for(number)

        # Generate initial outcome
        outcome = choose_outcome(rng, scenario)

        # --------------------------------------------------
        # 4. Customer identity and consent handling
        # --------------------------------------------------
        customer_number = rng.randint(1, CUSTOMER_COUNT)

        candidate_customer_id = f"CUS-{customer_number:06d}"

        if scenario == "incorrect_identity_merge":

            # Select a customer who explicitly denied consent
            candidate_customer_id = rng.choice(
                denied_customer_ids
            )

            customer_number = int(
                candidate_customer_id.split("-")[1]
            )

            # Never attach this customer to the session
            customer_id = None

        elif consent_map[candidate_customer_id] == "granted":

            # Identity linking is allowed
            customer_id = candidate_customer_id

        else:

            # Denied or unknown consent: keep session anonymous
            customer_id = None

        anonymous_id = f"ANON-{number:08d}"

        # --------------------------------------------------
        # 5. Session information
        # --------------------------------------------------
        started = BASE_TIME + timedelta(
            minutes=number % 43200
        )

        session_channel = rng.choice(CHANNELS)

        sessions.append({
            "session_id": session_id,
            "customer_id": customer_id,
            "anonymous_id": anonymous_id,
            "device_id": f"DEVICE-{rng.randint(1, 20000):06d}",
            "channel": session_channel,
            "device_type": rng.choice(
                ["desktop", "mobile", "tablet"]
            ),
            "started_at": started,
            "ended_at": started + timedelta(minutes=15),
            "is_bot_candidate": scenario == "bot_traffic",
            "lifecycle_state": "completed",
        })

        # --------------------------------------------------
        # 6. Generate event sequence
        # --------------------------------------------------
        event_types = build_event_types(
            outcome, scenario, rng
        )

        cart_id = f"CART-{number:08d}"
        order_id = f"ORD-{number:08d}"
        ticket_id = f"TKT-{number:08d}"

        product_id = f"PRD-{rng.randint(1, PRODUCT_COUNT):06d}"
        page_id = f"PAG-{rng.randint(1, 30):04d}"

        has_cart = "add_to_cart" in event_types
        has_order = outcome == "converted"
        has_support = outcome == "support_contact"

        price = round(rng.uniform(500, 80000), 2)

        # --------------------------------------------------
        # 7. Generate cart information
        # --------------------------------------------------
        if has_cart:

            carts.append({
                "cart_id": cart_id,
                "customer_id": customer_id,
                "session_id": session_id,
                "status": "converted" if has_order else "abandoned",
            })

            cart_item_rows.append({
                "cart_id": cart_id,
                "product_id": product_id,
                "quantity": 1,
                "unit_price": price,
            })

        # --------------------------------------------------
        # 8. Generate order information
        # --------------------------------------------------
        if has_order:

            orders.append({
                "order_id": order_id,
                "customer_id": customer_id,
                "session_id": session_id,
                "total_amount": price,
                "payment_status": "success",
                "order_status": "completed",
                "ordered_at": started + timedelta(minutes=10),
            })

            order_item_rows.append({
                "order_id": order_id,
                "product_id": product_id,
                "quantity": 1,
                "unit_price": price,
            })

        # --------------------------------------------------
        # 9. Generate support ticket
        # --------------------------------------------------
        if has_support:

            tickets.append({
                "ticket_id": ticket_id,
                "customer_id": customer_id,
                "session_id": session_id,
                "issue_category": "payment_issue",
                "priority": "normal",
                "status": "open",
            })

        # --------------------------------------------------
        # 10. Assign experiment
        # --------------------------------------------------
        experiment_rows.append({
            "session_id": session_id,
            "experiment_id": f"EXP-2026-{rng.randint(1, 5):06d}",
            "variant": rng.choice(["control", "variant_a"]),
        })

        # --------------------------------------------------
        # 11. Generate immutable journey events
        # --------------------------------------------------
        duplicate_seen = False

        for event_index, event_type in enumerate(
            event_types, start=1
        ):

            event_id = (
                f"EVT-{session_id}-{event_index:06d}"
            )

            event_time = started + timedelta(
                seconds=event_index * 30
            )

            delay = rng.randint(1, 20)

            # Inject out-of-order ingestion
            if (
                scenario == "out_of_order"
                and event_index == 10
            ):
                delay = 600

            if (
                scenario == "out_of_order"
                and event_index == 11
            ):
                delay = 1

            ingestion_time = event_time + timedelta(
                seconds=delay
            )

            channel = session_channel

            if event_type == "support_contact":
                channel = "support"

            elif event_type in [
                "payment_success",
                "payment_initiated",
            ]:
                channel = "purchase"

            elif event_type == "app_open":
                channel = "mobile_app"

            dedup_key = (
                f"{session_id}:{event_index}:{event_type}"
            )

            source_event_id = event_id

            # Detect repeated payment events using the same key
            if event_type == "payment_success":

                dedup_key = f"{order_id}:payment_success"

                if duplicate_seen:
                    source_event_id = f"PAYMENT-{order_id}"

                else:
                    duplicate_seen = True

            is_late = delay > 120

            events.append({
                "event_id": event_id,
                "session_id": session_id,
                "customer_id": customer_id,
                "page_id": (
                    page_id
                    if event_type in [
                        "page_view",
                        "product_view",
                    ]
                    else None
                ),
                "event_type": event_type,
                "channel": channel,
                "event_timestamp": event_time,
                "ingestion_timestamp": ingestion_time,
                "deduplication_key": dedup_key,
                "source_event_id": source_event_id,
                "is_late": is_late,
                "payload": {
                    "product_id": product_id,
                    "bot_signal": scenario == "bot_traffic",
                    "latency_ms": rng.randint(50, 5000),
                },
            })

            # Ground truth for duplicate conversion
            if (
                scenario == "duplicate_conversion"
                and event_index == EVENTS_PER_SESSION
            ):

                truth_rows.append({
                    "ground_truth_id": f"GT-{session_id}-DUP",
                    "session_id": session_id,
                    "event_id": event_id,
                    "scenario_type": scenario,
                    "expected_label": "duplicate",
                    "expected_decision": "count_once",
                    "explanation": (
                        "Two payment events reference the same order."
                    ),
                })

        # --------------------------------------------------
        # 12. Derive final outcome from generated events
        # --------------------------------------------------
        if "payment_success" in event_types:

            final_outcome = "converted"
            conversion_value = price
            dropoff_stage = None

        elif "support_contact" in event_types:

            final_outcome = "support_contact"
            conversion_value = 0
            dropoff_stage = "support"

        elif "add_to_cart" in event_types:

            final_outcome = "abandoned"
            conversion_value = 0
            dropoff_stage = "checkout"

        else:

            final_outcome = "browse_only"
            conversion_value = 0
            dropoff_stage = "product_discovery"

        outcomes.append({
            "outcome_id": f"OUT-{session_id}",
            "session_id": session_id,
            "customer_id": customer_id,
            "outcome_type": final_outcome,
            "funnel_stage_reached": (
                "purchase"
                if final_outcome == "converted"
                else dropoff_stage
            ),
            "conversion_value": conversion_value,
            "dropoff_stage": dropoff_stage,
            "rules_version": "v1",
        })

        # --------------------------------------------------
        # 13. Incorrect identity merge ground truth
        # --------------------------------------------------
        if scenario == "incorrect_identity_merge":

            identity_rows.append({
                "link_id": f"LNK-{number:08d}",
                "customer_id": candidate_customer_id,
                "anonymous_id": anonymous_id,
                "device_id": None,
                "consent_status": "denied",
                "link_status": "rejected",
                "valid_from": started,
                "decision_reason": (
                    "Identity link rejected: consent denied."
                ),
            })

            truth_rows.append({
                "ground_truth_id": f"GT-{session_id}-ID",
                "session_id": session_id,
                "scenario_type": scenario,
                "expected_label": "unauthorized_identity_link",
                "expected_decision": "reject_identity_link",
                "explanation": (
                    "Anonymous identity must not be linked without consent."
                ),
            })

        # --------------------------------------------------
        # 14. Out-of-order event ground truth
        # --------------------------------------------------
        elif scenario == "out_of_order":

            truth_rows.append({
                "ground_truth_id": f"GT-{session_id}-LATE",
                "session_id": session_id,
                "scenario_type": scenario,
                "expected_label": "late_event",
                "expected_decision": "order_by_event_timestamp",
                "explanation": (
                    "Ingestion timestamps do not preserve event order."
                ),
            })

        # --------------------------------------------------
        # 15. Bot traffic ground truth
        # --------------------------------------------------
        elif scenario == "bot_traffic":

            truth_rows.append({
                "ground_truth_id": f"GT-{session_id}-BOT",
                "session_id": session_id,
                "scenario_type": scenario,
                "expected_label": "bot",
                "expected_decision": "exclude_from_human_metrics",
                "explanation": (
                    "Session was generated with bot traffic signals."
                ),
            })

    # --------------------------------------------------
    # 16. Insert records in foreign-key dependency order
    # --------------------------------------------------
    conn.execute(insert(SessionRecord), sessions)

    if carts:
        conn.execute(insert(Cart), carts)

    if orders:
        conn.execute(insert(Order), orders)

    if tickets:
        conn.execute(insert(SupportTicket), tickets)

    conn.execute(insert(JourneyEvent), events)

    if cart_item_rows:
        conn.execute(insert(cart_items), cart_item_rows)

    if order_item_rows:
        conn.execute(insert(order_items), order_item_rows)

    conn.execute(
        insert(session_experiments),
        experiment_rows
    )

    conn.execute(insert(JourneyOutcome), outcomes)

    if identity_rows:
        conn.execute(insert(IdentityLink), identity_rows)

    if truth_rows:
        conn.execute(insert(GroundTruth), truth_rows)

    return len(sessions), len(events)



def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--sessions", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--reset", action="store_true")

    args = parser.parse_args()

    if args.sessions < 1:
        raise ValueError("Sessions must be greater than zero.")

    rng = random.Random(args.seed)

    with engine.begin() as conn:
        existing = conn.execute(
            text("SELECT COUNT(*) FROM sessions")
        ).scalar_one()

        if existing and not args.reset:
            raise RuntimeError(
                "Database already contains sessions. "
                "Use --reset only if you intend to erase existing data."
            )

        if args.reset:
            conn.execute(text("""
                TRUNCATE TABLE
                    event_state_history,
                    anomaly_records,
                    ground_truth,
                    identity_links,
                    journey_outcomes,
                    journey_events,
                    order_items,
                    cart_items,
                    session_experiments,
                    support_tickets,
                    orders,
                    carts,
                    sessions,
                    pages,
                    products,
                    experiments,
                    customers
                RESTART IDENTITY CASCADE
            """))

        generate_master_data(conn, rng)

    total_sessions = 0
    total_events = 0

    print(f"Starting generation: {args.sessions:,} sessions")

    for start in range(1, args.sessions + 1, BATCH_SIZE):
        end = min(start + BATCH_SIZE, args.sessions + 1)

        with engine.begin() as conn:
            session_count, event_count = generate_batch(
                conn, start, end, rng
            )

        total_sessions += session_count
        total_events += event_count

        print(
            f"Generated {total_sessions:,} sessions "
            f"and {total_events:,} events"
        )

    print("\nDATA GENERATION COMPLETE")
    print("Seed:", args.seed)
    print("Sessions:", total_sessions)
    print("Events:", total_events)
    print("Expected events:", total_sessions * EVENTS_PER_SESSION)


if __name__ == "__main__":
    main()
