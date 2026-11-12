# Journey Intelligence — Database Data Dictionary

## 1. Overview

Journey Intelligence is a multi-channel customer journey analytics platform designed to capture, analyze, and evaluate customer interactions across web, mobile, support, and purchase channels.

The database contains 17 tables covering customer identity, sessions, journey events, products, carts, orders, support tickets, experiments, outcomes, anomaly detection, and evaluation.

## 2. Database conventions

- Primary keys uniquely identify records.
- Foreign keys maintain referential integrity.
- Nullable fields are optional unless otherwise specified.
- `DateTime(timezone=True)` stores timezone-aware timestamps.
- `Numeric(12, 2)` stores decimal values with two decimal places.
- `JSON` stores structured event payloads.
- Bridge tables implement many-to-many relationships.
- Event history and ground-truth records are stored separately from source events.

## 3. Entity data dictionary

### 3.1 customers

**Purpose:** Stores customer information and consent status.

| Column             | Type                    | Required | Key / Default       | Description                |
| ------------------ | ----------------------- | -------- | ------------------- | -------------------------- |
| customer_id        | String                  | Yes      | PK                  | Unique customer identifier |
| email              | String                  | No       | Unique, indexed     | Customer email             |
| name               | String                  | No       | —                   | Customer name              |
| consent_status     | String                  | Yes      | Default: unknown    | Customer consent status    |
| consent_updated_at | DateTime(timezone=True) | No       | —                   | Last consent update        |
| created_at         | DateTime(timezone=True) | No       | Server default: now | Record creation time       |

### 3.2 sessions

**Purpose:** Represents an individual customer or anonymous browsing session.

| Column           | Type                    | Required | Key / Default                       | Description                  |
| ---------------- | ----------------------- | -------- | ----------------------------------- | ---------------------------- |
| session_id       | String                  | Yes      | PK                                  | Unique session identifier    |
| customer_id      | String                  | No       | FK → customers.customer_id, indexed | Associated customer          |
| anonymous_id     | String                  | No       | Indexed                             | Anonymous visitor identifier |
| device_id        | String                  | No       | —                                   | Device identifier            |
| channel          | String                  | Yes      | —                                   | Session channel              |
| device_type      | String                  | No       | —                                   | Device category              |
| started_at       | DateTime(timezone=True) | Yes      | —                                   | Session start time           |
| ended_at         | DateTime(timezone=True) | No       | —                                   | Session end time             |
| is_bot_candidate | Boolean                 | No       | Default: false                      | Potential bot indicator      |
| lifecycle_state  | String                  | No       | Default: active                     | Session lifecycle state      |
| created_at       | DateTime(timezone=True) | No       | Server default: now                 | Record creation time         |

### 3.3 pages

**Purpose:** Stores website or application pages associated with journey events.

| Column     | Type                    | Required | Key / Default            | Description            |
| ---------- | ----------------------- | -------- | ------------------------ | ---------------------- |
| page_id    | String                  | Yes      | PK                       | Unique page identifier |
| page_name  | String                  | Yes      | —                        | Page name              |
| page_url   | String                  | No       | —                        | Page URL               |
| page_type  | String                  | No       | —                        | Page category          |
| product_id | String                  | No       | FK → products.product_id | Associated product     |
| created_at | DateTime(timezone=True) | No       | Server default: now      | Record creation time   |

### 3.4 products

**Purpose:** Stores products available for customer browsing and purchasing.

| Column       | Type                    | Required | Key / Default       | Description               |
| ------------ | ----------------------- | -------- | ------------------- | ------------------------- |
| product_id   | String                  | Yes      | PK                  | Unique product identifier |
| product_name | String                  | Yes      | —                   | Product name              |
| category     | String                  | No       | —                   | Product category          |
| price        | Numeric(12, 2)          | Yes      | —                   | Product price             |
| status       | String                  | No       | Default: active     | Product status            |
| created_at   | DateTime(timezone=True) | No       | Server default: now | Record creation time      |

### 3.5 carts

**Purpose:** Stores shopping carts associated with sessions and customers.

| Column      | Type                    | Required | Key / Default                       | Description            |
| ----------- | ----------------------- | -------- | ----------------------------------- | ---------------------- |
| cart_id     | String                  | Yes      | PK                                  | Unique cart identifier |
| customer_id | String                  | No       | FK → customers.customer_id, indexed | Associated customer    |
| session_id  | String                  | Yes      | FK → sessions.session_id, indexed   | Associated session     |
| status      | String                  | No       | Default: active                     | Cart status            |
| created_at  | DateTime(timezone=True) | No       | Server default: now                 | Cart creation time     |
| updated_at  | DateTime(timezone=True) | No       | —                                   | Last cart update time  |

### 3.6 cart_items

**Purpose:** Bridge table connecting carts and products.

| Column     | Type           | Required | Key / Default                          | Description        |
| ---------- | -------------- | -------- | -------------------------------------- | ------------------ |
| cart_id    | String         | Yes      | Composite PK, FK → carts.cart_id       | Cart identifier    |
| product_id | String         | Yes      | Composite PK, FK → products.product_id | Product identifier |
| quantity   | Integer        | Yes      | Default: 1                             | Product quantity   |
| unit_price | Numeric(12, 2) | Yes      | —                                      | Price per unit     |

**Primary key:** (cart_id, product_id)

### 3.7 orders

**Purpose:** Stores customer purchase and payment information.

| Column         | Type                    | Required | Key / Default                       | Description             |
| -------------- | ----------------------- | -------- | ----------------------------------- | ----------------------- |
| order_id       | String                  | Yes      | PK                                  | Unique order identifier |
| customer_id    | String                  | No       | FK → customers.customer_id, indexed | Associated customer     |
| session_id     | String                  | No       | FK → sessions.session_id, indexed   | Associated session      |
| total_amount   | Numeric(12, 2)          | Yes      | —                                   | Total order amount      |
| payment_status | String                  | No       | Default: pending                    | Payment status          |
| order_status   | String                  | No       | Default: created                    | Order status            |
| ordered_at     | DateTime(timezone=True) | No       | —                                   | Order timestamp         |
| created_at     | DateTime(timezone=True) | No       | Server default: now                 | Record creation time    |

### 3.8 order_items

**Purpose:** Bridge table connecting orders and products.

| Column     | Type           | Required | Key / Default                          | Description        |
| ---------- | -------------- | -------- | -------------------------------------- | ------------------ |
| order_id   | String         | Yes      | Composite PK, FK → orders.order_id     | Order identifier   |
| product_id | String         | Yes      | Composite PK, FK → products.product_id | Product identifier |
| quantity   | Integer        | Yes      | —                                      | Purchased quantity |
| unit_price | Numeric(12, 2) | Yes      | —                                      | Price per unit     |

**Primary key:** (order_id, product_id)

### 3.9 support_tickets

**Purpose:** Tracks customer support requests associated with customers and sessions.

| Column         | Type                    | Required | Key / Default                       | Description              |
| -------------- | ----------------------- | -------- | ----------------------------------- | ------------------------ |
| ticket_id      | String                  | Yes      | PK                                  | Unique ticket identifier |
| customer_id    | String                  | No       | FK → customers.customer_id, indexed | Associated customer      |
| session_id     | String                  | No       | FK → sessions.session_id, indexed   | Associated session       |
| issue_category | String                  | No       | —                                   | Support issue category   |
| priority       | String                  | No       | Default: normal                     | Ticket priority          |
| status         | String                  | No       | Default: open                       | Ticket status            |
| created_at     | DateTime(timezone=True) | No       | Server default: now                 | Ticket creation time     |
| resolved_at    | DateTime(timezone=True) | No       | —                                   | Ticket resolution time   |

### 3.10 experiments

**Purpose:** Stores experiment information for journey experimentation and analysis.

| Column          | Type                    | Required | Key / Default       | Description                  |
| --------------- | ----------------------- | -------- | ------------------- | ---------------------------- |
| experiment_id   | String                  | Yes      | PK                  | Unique experiment identifier |
| experiment_name | String                  | Yes      | —                   | Experiment name              |
| status          | String                  | No       | Default: active     | Experiment status            |
| start_date      | Date                    | Yes      | —                   | Experiment start date        |
| end_date        | Date                    | No       | —                   | Experiment end date          |
| created_at      | DateTime(timezone=True) | No       | Server default: now | Record creation time         |

### 3.11 session_experiments

**Purpose:** Bridge table assigning experiments to sessions.

| Column        | Type                    | Required | Key / Default                                | Description                 |
| ------------- | ----------------------- | -------- | -------------------------------------------- | --------------------------- |
| session_id    | String                  | Yes      | Composite PK, FK → sessions.session_id       | Session identifier          |
| experiment_id | String                  | Yes      | Composite PK, FK → experiments.experiment_id | Experiment identifier       |
| variant       | String                  | Yes      | —                                            | Assigned experiment variant |
| assigned_at   | DateTime(timezone=True) | No       | Server default: now                          | Assignment timestamp        |

**Primary key:** (session_id, experiment_id)

### 3.12 journey_events

**Purpose:** Stores customer journey interactions across channels.

| Column              | Type                    | Required | Key / Default                       | Description                      |
| ------------------- | ----------------------- | -------- | ----------------------------------- | -------------------------------- |
| event_id            | String                  | Yes      | PK                                  | Unique event identifier          |
| session_id          | String                  | Yes      | FK → sessions.session_id, indexed   | Associated session               |
| customer_id         | String                  | No       | FK → customers.customer_id, indexed | Associated customer              |
| page_id             | String                  | No       | FK → pages.page_id                  | Associated page                  |
| event_type          | String                  | Yes      | Indexed                             | Event category                   |
| channel             | String                  | Yes      | —                                   | Event source channel             |
| event_timestamp     | DateTime(timezone=True) | Yes      | —                                   | Actual event occurrence time     |
| ingestion_timestamp | DateTime(timezone=True) | Yes      | Indexed                             | Event ingestion time             |
| deduplication_key   | String                  | No       | Indexed                             | Key used for duplicate detection |
| source_event_id     | String                  | No       | —                                   | Original source event identifier |
| is_late             | Boolean                 | No       | Default: false                      | Indicates a late-arriving event  |
| payload             | JSON                    | No       | —                                   | Additional event information     |
| created_at          | DateTime(timezone=True) | No       | Server default: now                 | Database record creation time    |

**Additional indexes:**

- (session_id, event_timestamp)
- (channel, event_type)

### 3.13 journey_outcomes

**Purpose:** Stores the final calculated outcome of a customer journey.

| Column               | Type                    | Required | Key / Default                            | Description                  |
| -------------------- | ----------------------- | -------- | ---------------------------------------- | ---------------------------- |
| outcome_id           | String                  | Yes      | PK                                       | Unique outcome identifier    |
| session_id           | String                  | Yes      | Unique FK → sessions.session_id, indexed | Associated session           |
| customer_id          | String                  | No       | FK → customers.customer_id               | Associated customer          |
| outcome_type         | String                  | Yes      | —                                        | Final journey outcome        |
| funnel_stage_reached | String                  | No       | —                                        | Highest funnel stage reached |
| conversion_value     | Numeric(12, 2)          | No       | Default: 0                               | Conversion amount            |
| dropoff_stage        | String                  | No       | —                                        | Journey drop-off stage       |
| calculated_at        | DateTime(timezone=True) | No       | Server default: now                      | Outcome calculation time     |
| rules_version        | String                  | Yes      | Default: v1                              | Rules version used           |

**Constraint:** A unique session_id allows at most one outcome per session.

### 3.14 identity_links

**Purpose:** Records identity stitching decisions and consent information.

| Column          | Type                    | Required | Key / Default                       | Description                      |
| --------------- | ----------------------- | -------- | ----------------------------------- | -------------------------------- |
| link_id         | String                  | Yes      | PK                                  | Unique identity link identifier  |
| customer_id     | String                  | Yes      | FK → customers.customer_id, indexed | Customer identifier              |
| anonymous_id    | String                  | Yes      | Indexed                             | Anonymous visitor identifier     |
| device_id       | String                  | No       | —                                   | Device identifier                |
| consent_status  | String                  | Yes      | —                                   | Consent at decision time         |
| link_status     | String                  | Yes      | Default: pending                    | Identity link decision status    |
| valid_from      | DateTime(timezone=True) | Yes      | —                                   | Link validity start              |
| valid_to        | DateTime(timezone=True) | No       | —                                   | Link validity end                |
| decision_reason | Text                    | No       | —                                   | Reason for the identity decision |
| created_at      | DateTime(timezone=True) | No       | Server default: now                 | Record creation time             |

### 3.15 anomaly_records

**Purpose:** Stores detected journey anomalies without deleting original source events.

| Column            | Type                    | Required | Key / Default                         | Description                  |
| ----------------- | ----------------------- | -------- | ------------------------------------- | ---------------------------- |
| anomaly_id        | String                  | Yes      | PK                                    | Unique anomaly identifier    |
| session_id        | String                  | No       | FK → sessions.session_id, indexed     | Associated session           |
| event_id          | String                  | No       | FK → journey_events.event_id, indexed | Associated event             |
| issue_type        | String                  | Yes      | Indexed                               | Type of detected anomaly     |
| severity          | String                  | Yes      | Default: medium                       | Anomaly severity             |
| detection_reason  | Text                    | Yes      | —                                     | Explanation of detection     |
| detection_rule    | String                  | Yes      | —                                     | Rule that detected the issue |
| resolution_status | String                  | Yes      | Default: open                         | Resolution status            |
| detected_at       | DateTime(timezone=True) | No       | Server default: now                   | Detection timestamp          |

### 3.16 ground_truth

**Purpose:** Stores expected labels and decisions for evaluating anomaly detection.

| Column            | Type                    | Required | Key / Default                         | Description                    |
| ----------------- | ----------------------- | -------- | ------------------------------------- | ------------------------------ |
| ground_truth_id   | String                  | Yes      | PK                                    | Unique ground-truth identifier |
| session_id        | String                  | No       | FK → sessions.session_id, indexed     | Associated session             |
| event_id          | String                  | No       | FK → journey_events.event_id, indexed | Associated event               |
| scenario_type     | String                  | Yes      | —                                     | Injected scenario category     |
| expected_label    | String                  | Yes      | —                                     | Expected anomaly label         |
| expected_decision | String                  | Yes      | —                                     | Expected system decision       |
| explanation       | Text                    | No       | —                                     | Explanation of expected result |
| rules_version     | String                  | Yes      | Default: v1                           | Evaluation rules version       |
| created_at        | DateTime(timezone=True) | No       | Server default: now                   | Record creation time           |

**Important:** Ground-truth records must be kept separate from detector input features to prevent evaluation leakage.

### 3.17 event_state_history

**Purpose:** Maintains an append-only history of event processing state changes.

| Column          | Type                    | Required | Key / Default                         | Description               |
| --------------- | ----------------------- | -------- | ------------------------------------- | ------------------------- |
| history_id      | String                  | Yes      | PK                                    | Unique history identifier |
| event_id        | String                  | Yes      | FK → journey_events.event_id, indexed | Associated event          |
| previous_state  | String                  | No       | —                                     | Previous processing state |
| new_state       | String                  | Yes      | —                                     | New processing state      |
| decision_reason | Text                    | No       | —                                     | Reason for state change   |
| processed_at    | DateTime(timezone=True) | No       | Server default: now                   | Processing timestamp      |

## 4. Relationship and cardinality summary

| Parent entity  | Child entity        | Relationship                           | Foreign key                  |
| -------------- | ------------------- | -------------------------------------- | ---------------------------- |
| customers      | sessions            | One-to-many; session customer optional | sessions.customer_id         |
| sessions       | journey_events      | One-to-many                            | journey_events.session_id    |
| customers      | journey_events      | One-to-many; event customer optional   | journey_events.customer_id   |
| products       | pages               | One-to-many; page product optional     | pages.product_id             |
| sessions       | carts               | One-to-many                            | carts.session_id             |
| customers      | carts               | One-to-many; cart customer optional    | carts.customer_id            |
| carts          | products            | Many-to-many                           | cart_items                   |
| sessions       | orders              | One-to-many; order session optional    | orders.session_id            |
| customers      | orders              | One-to-many; order customer optional   | orders.customer_id           |
| orders         | products            | Many-to-many                           | order_items                  |
| customers      | support_tickets     | One-to-many; ticket customer optional  | support_tickets.customer_id  |
| sessions       | support_tickets     | One-to-many; ticket session optional   | support_tickets.session_id   |
| sessions       | experiments         | Many-to-many                           | session_experiments          |
| sessions       | journey_outcomes    | One-to-zero-or-one                     | journey_outcomes.session_id  |
| customers      | identity_links      | One-to-many                            | identity_links.customer_id   |
| sessions       | anomaly_records     | One-to-many; anomaly session optional  | anomaly_records.session_id   |
| journey_events | anomaly_records     | One-to-many; anomaly event optional    | anomaly_records.event_id     |
| sessions       | ground_truth        | One-to-many; session optional          | ground_truth.session_id      |
| journey_events | ground_truth        | One-to-many; event optional            | ground_truth.event_id        |
| journey_events | event_state_history | One-to-many                            | event_state_history.event_id |

## 5. Indexes and constraints

### Primary keys

Every entity has a primary key. The bridge tables use composite primary keys:

- cart_items: (cart_id, product_id)
- order_items: (order_id, product_id)
- session_experiments: (session_id, experiment_id)

### Unique constraints

- customers.email is unique.
- journey_outcomes.session_id is unique.

### Explicit performance indexes

- journey_events(session_id, event_timestamp)
- journey_events(channel, event_type)
- orders(customer_id, ordered_at)

Additional individual indexes are defined on selected foreign keys and frequently queried columns in the SQLAlchemy models.

## 6. Validation considerations

The data-quality validation layer should check:

1. Primary
