# Scope & Anomaly Log

This document details the scope of the anomaly detection engine, exactly what data issues were found in the provided `Expenses Export.csv`, how each was handled, and the underlying database schema used to persist and audit these records.

## Anomaly Log

When parsing the `Expenses Export.csv` provided for the assessment, the application pipeline evaluates each row using stateless rule engines. Here is the log of the data problems found and how the engine handled them:

### 1. Extraneous/Duplicate Rows
- **Data Problem Found**: Row 6 (`08-02-2026,dinner - marina bites,Dev,3200,INR...`) is almost identical to Row 5, and Row 25 (`11-03-2026,Thalassa dinner,Rohan,2450,INR...`) is practically identical to Row 24.
- **Action Taken (WARNING)**: The `duplicate_expense` rule hashes the date, amount, and normalized description. When it detects a collision, it flags the row with a `WARNING` severity `DUPLICATE_EXPENSE` anomaly. The row is imported but highlighted to the user on the dashboard.

### 2. Missing Fields
- **Data Problem Found**: Row 13 (`22-02-2026,House cleaning supplies,,780...`) is missing the `paid_by` (payer) field.
- **Action Taken (WARNING)**: Because the `paid_by` field is missing, the engine flags a `MISSING_PAYER` anomaly with `WARNING` severity. The system imports it but leaves the payer `null`, expecting manual reconciliation.
- **Data Problem Found**: Row 28 (`15-03-2026,Groceries DMart,Priya,2105,,equal...`) is missing the `currency` field.
- **Action Taken (INFO)**: The `missing_currency` rule flags this with an `INFO` anomaly, assuming `INR` or `USD` based on heuristics, but explicitly marking that currency was derived.

### 3. Invalid/Zero Amounts
- **Data Problem Found**: Row 7 (`10-02-2026,Electricity Feb,Aisha,"1,200"...`) contains commas, and Row 10 contains high precision `899.995`.
- **Action Taken (INFO)**: The normalizer perfectly strips commas and rounds precision to 2 decimal places. `INFO` anomalies (`AMOUNT_FORMAT_NORMALIZED` and `AMOUNT_PRECISION_NORMALIZED`) are generated for audit transparency.
- **Data Problem Found**: Row 31 (`22-03-2026,Dinner order Swiggy,Priya,0...`) has a zero amount.
- **Action Taken (REJECTED)**: The `zero_amount` rule rejects the expense entirely (`ZERO_AMOUNT` anomaly), as zero-value transactions clutter the ledger.

### 4. Ambiguous Dates
- **Data Problem Found**: Row 27 (`Mar-14,Airport cab...`) has a completely different date format, and Row 34 (`04-05-2026...`) has a note indicating confusion between April 5 and May 4.
- **Action Taken (WARNING)**: The normalizer uses robust parsing (via dateutil) to resolve `Mar-14` to the current year, and warns on `04-05-2026` via the `AMBIGUOUS_DATE` anomaly to prompt user review for DD-MM vs MM-DD conflicts.

### 5. Settlements and Refunds
- **Data Problem Found**: Row 14 (`Rohan paid Aisha back, 5000`) is a settlement, not an expense. Row 26 (`Parasailing refund, -30`) is a refund.
- **Action Taken (IMPORTED)**: The engine detects negative amounts and/or keywords like "refund", "paid back", or "deposit" in the description. It automatically re-categorizes the `expense_type` to `REFUND` or `SETTLEMENT` and generates `INFO` anomalies (`SETTLEMENT_TRANSACTION`, `REFUND_TRANSACTION`). No participant shares are generated for settlements.

### 6. Participant & Split Conflicts
- **Data Problem Found**: Row 15 (`percentage` split) has percentages that do not sum to 100% (30+30+30+20 = 110%).
- **Action Taken (WARNING)**: The `split_validation` rule checks percentage math. It flags an `INVALID_PERCENTAGE_SPLIT` warning but imports the data, trusting the user's manual override.
- **Data Problem Found**: Row 36 (`Meera still in group list`) but Meera left in March.
- **Action Taken (INFO)**: Detected as an anomaly since the group changed.
- **Data Problem Found**: Row 42 (`split_type says equal but someone added shares`).
- **Action Taken (WARNING)**: The rule detects `split_type=equal` but the presence of `split_details`. It flags a `CONFLICTING_SPLIT_INFO` warning and defaults to the explicitly listed shares.

---

## Database Schema

The database relies on an asynchronous PostgreSQL backend with SQLAlchemy 2.0 ORM. The schema consists of 5 core tables that guarantee relational integrity:

1. **`users`**
   - Stores all unique participants involved in the ledger.
   - `id` (UUID), `name`, `normalized_name` (for deduplication), `is_guest` (boolean).

2. **`import_reports`**
   - The top-level audit log for a single CSV upload.
   - `id` (UUID), `filename`, `imported_at`, `total_rows`, `imported_count`, `rejected_count`, `warning_count`, `report_json` (Stores the fully generated anomaly JSON for fast retrieval).

3. **`expenses`**
   - The normalized ledger entries.
   - `id` (UUID), `import_id` (FK), `payer_id` (FK), `row_number`, `expense_date`, `description`, `amount`, `currency`, `split_type`, `expense_type` (Enum: EXPENSE, SETTLEMENT, REFUND), `status` (Enum: IMPORTED, WARNING, REJECTED), `raw_row` (JSON).

4. **`expense_participants`**
   - A junction table mapping how a single expense is divided.
   - `id` (UUID), `expense_id` (FK), `user_id` (FK), `share_amount`, `share_percentage`, `share_weight`.

5. **`anomalies`**
   - Every triggered rule is logged here for the dashboard.
   - `id` (UUID), `import_id` (FK), `expense_id` (FK, nullable), `row_number`, `category` (Enum), `severity` (Enum: ERROR, WARNING, INFO), `reason`, `resolution`.
