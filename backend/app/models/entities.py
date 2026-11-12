
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Date,
    ForeignKey, Numeric, Text, JSON, Table, Index,
    UniqueConstraint
)
from sqlalchemy.sql import func

from app.db.database import Base


# =====================================================
# BRIDGE TABLE 1: CART <-> PRODUCT
# Cardinality: Many-to-Many
# =====================================================

cart_items = Table(
    "cart_items",
    Base.metadata,
    Column("cart_id", String, ForeignKey("carts.cart_id"), primary_key=True),
    Column("product_id", String, ForeignKey("products.product_id"), primary_key=True),
    Column("quantity", Integer, nullable=False, default=1),
    Column("unit_price", Numeric(12, 2), nullable=False),
)


# =====================================================
# BRIDGE TABLE 2: ORDER <-> PRODUCT
# Cardinality: Many-to-Many
# =====================================================

order_items = Table(
    "order_items",
    Base.metadata,
    Column("order_id", String, ForeignKey("orders.order_id"), primary_key=True),
    Column("product_id", String, ForeignKey("products.product_id"), primary_key=True),
    Column("quantity", Integer, nullable=False),
    Column("unit_price", Numeric(12, 2), nullable=False),
)


# =====================================================
# BRIDGE TABLE 3: SESSION <-> EXPERIMENT
# Cardinality: Many-to-Many
# =====================================================

session_experiments = Table(
    "session_experiments",
    Base.metadata,
    Column("session_id", String, ForeignKey("sessions.session_id"), primary_key=True),
    Column("experiment_id", String, ForeignKey("experiments.experiment_id"), primary_key=True),
    Column("variant", String, nullable=False),
    Column("assigned_at", DateTime(timezone=True), server_default=func.now()),
)


# =====================================================
# 1. CUSTOMER
# One customer can have multiple sessions.
# =====================================================

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=True, index=True)
    name = Column(String, nullable=True)

    consent_status = Column(String, nullable=False, default="unknown")
    consent_updated_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# =====================================================
# 2. SESSION
# One session belongs to zero or one customer.
# One session contains many journey events.
# =====================================================

class SessionRecord(Base):
    __tablename__ = "sessions"

    session_id = Column(String, primary_key=True)

    customer_id = Column(
        String, ForeignKey("customers.customer_id"), nullable=True, index=True
    )

    anonymous_id = Column(String, nullable=True, index=True)
    device_id = Column(String, nullable=True)

    channel = Column(String, nullable=False)
    device_type = Column(String, nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    is_bot_candidate = Column(Boolean, default=False)
    lifecycle_state = Column(String, default="active")

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# =====================================================
# 3. PAGE
# One page can appear in many journey events.
# =====================================================

class Page(Base):
    __tablename__ = "pages"

    page_id = Column(String, primary_key=True)
    page_name = Column(String, nullable=False)
    page_url = Column(String, nullable=True)
    page_type = Column(String, nullable=True)

    product_id = Column(
        String, ForeignKey("products.product_id"), nullable=True
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# =====================================================
# 4. PRODUCT
# One product can appear in many cart/order items.
# =====================================================

class Product(Base):
    __tablename__ = "products"

    product_id = Column(String, primary_key=True)
    product_name = Column(String, nullable=False)
    category = Column(String, nullable=True)

    price = Column(Numeric(12, 2), nullable=False)
    status = Column(String, default="active")

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# =====================================================
# 5. CART
# One customer/session can have multiple carts.
# One cart can contain multiple products.
# =====================================================

class Cart(Base):
    __tablename__ = "carts"

    cart_id = Column(String, primary_key=True)

    customer_id = Column(
        String, ForeignKey("customers.customer_id"), nullable=True, index=True
    )

    session_id = Column(
        String, ForeignKey("sessions.session_id"), nullable=False, index=True
    )

    status = Column(String, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True)


# =====================================================
# 6. ORDER
# One customer/session can have multiple orders.
# =====================================================

class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String, primary_key=True)

    customer_id = Column(
        String, ForeignKey("customers.customer_id"), nullable=True, index=True
    )

    session_id = Column(
        String, ForeignKey("sessions.session_id"), nullable=True, index=True
    )

    total_amount = Column(Numeric(12, 2), nullable=False)
    payment_status = Column(String, default="pending")
    order_status = Column(String, default="created")

    ordered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# =====================================================
# 7. SUPPORT TICKET
# A customer/session can have multiple support tickets.
# =====================================================

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    ticket_id = Column(String, primary_key=True)

    customer_id = Column(
        String, ForeignKey("customers.customer_id"), nullable=True, index=True
    )

    session_id = Column(
        String, ForeignKey("sessions.session_id"), nullable=True, index=True
    )

    issue_category = Column(String, nullable=True)
    priority = Column(String, default="normal")
    status = Column(String, default="open")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)


# =====================================================
# 8. EXPERIMENT
# One experiment can be assigned to multiple sessions.
# =====================================================

class Experiment(Base):
    __tablename__ = "experiments"

    experiment_id = Column(String, primary_key=True)
    experiment_name = Column(String, nullable=False)

    status = Column(String, default="active")
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# =====================================================
# 9. JOURNEY EVENT
# One session can contain many events.
# Event history is preserved.
# =====================================================

class JourneyEvent(Base):
    __tablename__ = "journey_events"

    event_id = Column(String, primary_key=True)

    session_id = Column(
        String, ForeignKey("sessions.session_id"), nullable=False, index=True
    )

    customer_id = Column(
        String, ForeignKey("customers.customer_id"), nullable=True, index=True
    )

    page_id = Column(
        String, ForeignKey("pages.page_id"), nullable=True
    )

    event_type = Column(String, nullable=False, index=True)
    channel = Column(String, nullable=False)

    event_timestamp = Column(DateTime(timezone=True), nullable=False)
    ingestion_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    deduplication_key = Column(String, nullable=True, index=True)
    source_event_id = Column(String, nullable=True)

    is_late = Column(Boolean, default=False)
    payload = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# =====================================================
# 10. JOURNEY OUTCOME
# One session has at most one final outcome.
# =====================================================

class JourneyOutcome(Base):
    __tablename__ = "journey_outcomes"

    outcome_id = Column(String, primary_key=True)

    session_id = Column(
        String,
        ForeignKey("sessions.session_id"),
        nullable=False,
        unique=True,
        index=True
    )

    customer_id = Column(
        String, ForeignKey("customers.customer_id"), nullable=True
    )

    outcome_type = Column(String, nullable=False)
    funnel_stage_reached = Column(String, nullable=True)

    conversion_value = Column(Numeric(12, 2), default=0)
    dropoff_stage = Column(String, nullable=True)

    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    rules_version = Column(String, nullable=False, default="v1")


# =====================================================
# PERFORMANCE INDEXES
# =====================================================

Index(
    "ix_events_session_timestamp",
    JourneyEvent.session_id,
    JourneyEvent.event_timestamp
)

Index(
    "ix_events_channel_type",
    JourneyEvent.channel,
    JourneyEvent.event_type
)

Index(
    "ix_orders_customer_date",
    Order.customer_id,
    Order.ordered_at
)

# =====================================================
# 11. IDENTITY LINKS
# Tracks identity stitching and consent decisions.
# =====================================================

class IdentityLink(Base):
    __tablename__ = "identity_links"

    link_id = Column(String, primary_key=True)

    customer_id = Column(
        String, ForeignKey("customers.customer_id"), nullable=False, index=True
    )

    anonymous_id = Column(String, nullable=False, index=True)
    device_id = Column(String, nullable=True)

    consent_status = Column(String, nullable=False)
    link_status = Column(String, nullable=False, default="pending")

    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_to = Column(DateTime(timezone=True), nullable=True)

    decision_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# =====================================================
# 12. ANOMALY RECORDS
# Stores detected issues without deleting source events.
# =====================================================

class AnomalyRecord(Base):
    __tablename__ = "anomaly_records"

    anomaly_id = Column(String, primary_key=True)

    session_id = Column(
        String, ForeignKey("sessions.session_id"), nullable=True, index=True
    )

    event_id = Column(
        String, ForeignKey("journey_events.event_id"), nullable=True, index=True
    )

    issue_type = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False, default="medium")

    detection_reason = Column(Text, nullable=False)
    detection_rule = Column(String, nullable=False)

    resolution_status = Column(String, nullable=False, default="open")
    detected_at = Column(DateTime(timezone=True), server_default=func.now())


# =====================================================
# 13. GROUND TRUTH
# Separate evaluation labels. Never expose as input features.
# =====================================================

class GroundTruth(Base):
    __tablename__ = "ground_truth"

    ground_truth_id = Column(String, primary_key=True)

    session_id = Column(
        String, ForeignKey("sessions.session_id"), nullable=True, index=True
    )

    event_id = Column(
        String, ForeignKey("journey_events.event_id"), nullable=True, index=True
    )

    scenario_type = Column(String, nullable=False)
    expected_label = Column(String, nullable=False)
    expected_decision = Column(String, nullable=False)

    explanation = Column(Text, nullable=True)
    rules_version = Column(String, nullable=False, default="v1")

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# =====================================================
# 14. EVENT STATE HISTORY
# Append-only processing history.
# =====================================================

class EventStateHistory(Base):
    __tablename__ = "event_state_history"

    history_id = Column(String, primary_key=True)

    event_id = Column(
        String, ForeignKey("journey_events.event_id"), nullable=False, index=True
    )

    previous_state = Column(String, nullable=True)
    new_state = Column(String, nullable=False)

    decision_reason = Column(Text, nullable=True)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
