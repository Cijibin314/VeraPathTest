
# Verapath Database Schema

This document outlines the database schema for the Verapath project, as defined in `analytics/models.py`.

## Core Models

The database revolves around a few core concepts: Patients, Providers, Payers, and the Referrals that connect them.

### `Patient`

Represents an individual patient. To protect privacy, the patient's real ID is stored as `original_id` and a hashed `pseudonym` is used for display.

| Field         | Type                      | Description                                                  |
|---------------|---------------------------|--------------------------------------------------------------|
| `id`          | `BigAutoField` (Primary Key) | Auto-incrementing integer.                                   |
| `original_id` | `CharField(max_length=120)` | The patient's unique identifier from the source system (e.g., EHR). |
| `pseudonym`   | `CharField(max_length=64)`  | A SHA256 hash of the `original_id`, used for de-identification. |

### `Provider`

Represents a healthcare provider or specialist.

| Field          | Type                      | Description                                      |
|----------------|---------------------------|--------------------------------------------------|
| `id`           | `BigAutoField` (Primary Key) | Auto-incrementing integer.                       |
| `npi`          | `CharField(max_length=20)`  | The provider's unique National Provider Identifier. |
| `full_name`    | `CharField(max_length=200)` | The provider's full name.                        |
| `specialty`    | `CharField(max_length=120)` | The primary specialty of the provider.           |
| `subspecialty` | `CharField(max_length=120)` | The provider's sub-specialty (optional).         |
| `city`         | `CharField(max_length=100)` | The city where the provider practices (optional). |
| `state`        | `CharField(max_length=50)`  | The state where the provider practices (optional).  |

### `Payer`

Represents an insurance company or payer.

| Field  | Type                      | Description                         |
|--------|---------------------------|-------------------------------------|
| `id`   | `BigAutoField` (Primary Key) | Auto-incrementing integer.          |
| `code` | `CharField(max_length=64)`  | The payer's unique code or identifier. |
| `name` | `CharField(max_length=200)` | The payer's full name.              |

---

## Transactional Models

These models represent events and transactions within the system.

### `Referral`

This is the central model in the application, representing a single referral of a `Patient` to a `Provider`.

| Field                    | Type                         | Description                                                                 |
|--------------------------|------------------------------|-----------------------------------------------------------------------------|
| `id`                     | `BigAutoField` (Primary Key)    | Auto-incrementing integer.                                                  |
| `patient`                | `ForeignKey` to `Patient`    | The patient being referred. (Many-to-one)                                   |
| `provider`               | `ForeignKey` to `Provider`   | The provider the patient is being referred to. (Many-to-one)                |
| `payer`                  | `ForeignKey` to `Payer`      | The patient's insurance payer for this referral (optional). (Many-to-one)     |
| `specialty`              | `CharField(max_length=120)`  | The specialty requested for the referral (e.g., Cardiology).                |
| `status`                 | `CharField(max_length=20)`   | The current status of the referral (e.g., `pending`, `scheduled`, `completed`). |
| `in_network`             | `BooleanField`               | Whether the referral is to an in-network provider. Defaults to `True`.      |
| `cost_value`             | `DecimalField`               | The cost or value associated with this referral.                            |
| `referral_date`          | `DateField`                  | The date the referral was created.                                          |
| `suggested_provider_ids` | `CharField(max_length=200)`  | A comma-separated list of `Provider` IDs suggested as alternatives.         |
| `created_at`             | `DateTimeField`              | Timestamp when the referral was first created.                              |
| `ack_at`                 | `DateTimeField`              | Timestamp when the referral was acknowledged (optional).                    |
| `scheduled_at`           | `DateTimeField`              | Timestamp when the referral was scheduled (optional).                       |
| `completed_at`           | `DateTimeField`              | Timestamp when the referral was completed (optional).                       |
| `cancelled_at`           | `DateTimeField`              | Timestamp when the referral was cancelled (optional).                       |

### `ReferralHistory`

Tracks the status changes of a `Referral` over time.

| Field      | Type                         | Description                                           |
|------------|------------------------------|-------------------------------------------------------|
| `id`       | `BigAutoField` (Primary Key)    | Auto-incrementing integer.                            |
| `referral` | `ForeignKey` to `Referral`   | The referral this history entry belongs to. (Many-to-one) |
| `at`       | `DateTimeField`              | The timestamp of the status change.                   |
| `status`   | `CharField(max_length=20)`   | The status that the referral was changed to.          |

### `Invoice`

Represents an invoice generated based on retained revenue from in-network referrals.

| Field              | Type                         | Description                                           |
|--------------------|------------------------------|-------------------------------------------------------|
| `id`               | `BigAutoField` (Primary Key)    | Auto-incrementing integer.                            |
| `period_start`     | `DateField`                  | The start date of the invoice period.                 |
| `period_end`       | `DateField`                  | The end date of the invoice period.                   |
| `retained_revenue` | `DecimalField`               | Total retained revenue for the period.                |
| `fee_rate`         | `DecimalField`               | The fee rate used to calculate the amount due.        |
| `amount_due`       | `DecimalField`               | The final amount due for the invoice.                 |
| `is_paid`          | `BooleanField`               | Whether the invoice has been paid. Defaults to `False`. |
| `created_at`       | `DateTimeField`              | Timestamp when the invoice was generated.             |

---

## Analytics Models

### `Metric`

A generic model to store computed metrics for dashboard display.

| Field         | Type                         | Description                                      |
|---------------|------------------------------|--------------------------------------------------|
| `id`          | `BigAutoField` (Primary Key)    | Auto-incrementing integer.                       |
| `name`        | `CharField(max_length=100)`  | The name of the metric (e.g., `in_network_rate`). |
| `value`       | `FloatField`                 | The computed value of the metric.                |
| `computed_at` | `DateTimeField`              | Timestamp when the metric was computed.          |
