# Anomaly Analysis — Expenses Export CSV

**Analyzed on:** 2026-06-14  
**File:** `Expenses Export.csv`  
**Total rows:** 42  
**Columns:** `date`, `description`, `paid_by`, `amount`, `currency`, `split_type`, `split_with`, `split_details`, `notes`

---

## Summary Table

| Anomaly Category | Count | Severity |
|---|---|---|
| Duplicate / Near-duplicate expense | 3 | ERROR |
| Missing payer (`paid_by` empty) | 1 | ERROR |
| Missing currency | 1 | ERROR |
| Ambiguous / unparseable date | 2 | WARNING |
| Zero amount (possible placeholder) | 1 | WARNING |
| Non-standard amount format (comma in number) | 1 | WARNING |
| Irrational decimal precision (sub-paisa) | 1 | WARNING |
| Settlement transaction | 2 | WARNING |
| Refund transaction (negative amount) | 1 | WARNING |
| Unknown / guest participant | 1 | WARNING |
| Stale participant (moved out, still listed) | 1 | WARNING |
| Name inconsistency (same person, different name) | 2 | WARNING |
| Conflicting split type vs split details | 1 | WARNING |
| Percentage split that doesn't sum to 100% | 1 | WARNING |

**Total distinct anomalies detected: 18**

---

## 1. Duplicate / Near-Duplicate Expenses

### 1a. Exact duplicate — Row 4 & Row 5

| Field | Row 4 | Row 5 |
|---|---|---|
| date | 08-02-2026 | 08-02-2026 |
| description | `Dinner at Marina Bites` | `dinner - marina bites` |
| paid_by | Dev | Dev |
| amount | 3200 | 3200 |
| currency | INR | INR |

**Assessment:** Same event entered twice with slightly different description casing and punctuation. Row 5 has no notes; Row 4 has `Dev visiting for the weekend`. These are the same expense.

**Resolution strategy:** Flag both as `DUPLICATE_EXPENSE`. Keep Row 4 (more descriptive). Reject Row 5.

---

### 1b. Conflicting duplicate — Row 23 & Row 24

| Field | Row 23 | Row 24 |
|---|---|---|
| date | 11-03-2026 | 11-03-2026 |
| description | `Dinner at Thalassa` | `Thalassa dinner` |
| paid_by | Aisha | Rohan |
| amount | 2400 | 2450 |
| currency | INR | INR |

**Assessment:** Row 24 notes explicitly say *"Aisha also logged this I think hers is wrong"*. Same event, different payer and slightly different amount — a data entry conflict, not just a copy-paste duplicate.

**Resolution strategy:** Flag both as `DUPLICATE_EXPENSE` with severity `ERROR`. Cannot auto-resolve because both the payer and the amount differ — requires manual review. Import both as `status=REJECTED` with the anomaly record referencing both rows.

---

### 1c. Chronological out-of-order suggesting possible duplicate context — Row 33

Row 33 has date `04-05-2026` (May 4th) but note says *"is this April 5 or May 4? format is a mess"*. Its neighbors are all in April. See Section 5 (Ambiguous Date) for full analysis.

---

## 2. Missing Payer

### Row 12 — House cleaning supplies

```
date: 22-02-2026
description: House cleaning supplies
paid_by: (empty)
amount: 780
notes: can't remember who paid
```

**Assessment:** `paid_by` is required to track who is owed money. The note confirms deliberate omission.

**Resolution strategy:** Flag as `MISSING_PAYER` with severity `ERROR`. Import with `status=WARNING` and `payer_id=NULL` (nullable FK in schema). Include in anomaly report. Cannot be auto-corrected.

---

## 3. Missing Currency

### Row 27 — Groceries DMart (15-03-2026)

```
paid_by: Priya
amount: 2105
currency: (empty)
notes: forgot to set currency
```

**Assessment:** Currency is required for correct financial calculations. The note confirms it was simply forgotten. All surrounding expenses in the same date range are `INR`.

**Resolution strategy:** Flag as `MISSING_CURRENCY` with severity `ERROR`. Apply normalization: infer `INR` based on contextual majority currency and record the transformation in the transformation log. Import with `status=WARNING` and anomaly note documenting the inference.

---

## 4. Ambiguous / Unparseable Dates

### Row 26 — Airport cab: `Mar-14`

```
date: Mar-14
```

**Assessment:** Does not conform to the predominant `DD-MM-YYYY` format seen in all other rows. Could mean:
- March 14, 2026 (most likely given Goa trip context, rows 18–25 are all in early March)
- March 2014 (extremely unlikely given context)

**Resolution strategy:** Flag as `AMBIGUOUS_DATE` with severity `WARNING`. Infer `14-03-2026` from surrounding rows (the Goa trip ends on rows 21–25 dated 10–12 March; row 27 is 15-03-2026). Normalize to `2026-03-14`. Record transformation.

---

### Row 33 — Deep cleaning service: `04-05-2026`

```
date: 04-05-2026
notes: is this April 5 or May 4? format is a mess
```

**Assessment:** `04-05-2026` is parsed as April 5th under `DD-MM-YYYY` but the note explicitly flags uncertainty. If the format were `MM-DD-YYYY`, it would be May 4th.

The surrounding context: rows 34–42 are all April 2026 (01-04-2026 onwards). This row appears *before* Row 34 (April rent, 01-04-2026) in the CSV, which suggests it may have been entered out of order.

**Resolution strategy:** Flag as `AMBIGUOUS_DATE` with severity `WARNING`. Under the dominant `DD-MM-YYYY` format, parse as `2026-05-04` (May 4). Import with `status=WARNING`. Note that under DD-MM-YYYY, row 33 would chronologically fall *after* the April entries — consistent with the out-of-order note but not necessarily wrong.

---

## 5. Zero Amount

### Row 30 — Dinner order Swiggy

```
date: 22-03-2026
amount: 0
notes: counted twice earlier - fixing later
```

**Assessment:** An amount of 0 has no financial impact and the note implies this is a placeholder/correction acknowledgement, not a real expense.

**Resolution strategy:** Flag as `ZERO_AMOUNT` with severity `WARNING`. Import with `status=REJECTED`. The note makes intent clear: this is not a real expense entry.

---

## 6. Non-Standard Amount Format

### Row 6 — Electricity Feb

```
amount: "1,200"
```

**Assessment:** Amount contains a comma used as thousands separator. CSV parsers will read this as a string. Must be stripped of the comma before numeric parsing.

**Resolution strategy:** Flag as `AMOUNT_FORMAT_NORMALIZED` in transformation log. Strip commas, parse as `1200.00`. Not an error — this is a normalization step.

---

## 7. Irrational Decimal Precision

### Row 9 — Cylinder refill

```
amount: 899.995
```

**Assessment:** INR does not support fractions of paise (3 decimal places). Likely a data entry artifact (possibly a spreadsheet formula result).

**Resolution strategy:** Flag as `AMOUNT_PRECISION_NORMALIZED` in transformation log. Round to 2 decimal places → `900.00`. Severity: INFO.

---

## 8. Settlement Transaction

### Row 13 — Rohan paid Aisha back

```
description: Rohan paid Aisha back
paid_by: Rohan
amount: 5000
split_type: (empty)
split_with: Aisha
notes: this is a settlement not an expense??
```

**Assessment:** The note explicitly identifies this as a settlement, not a shared expense. There's no split type. This is a debt repayment, not an expense to be split.

**Resolution strategy:** Flag as `SETTLEMENT_TRANSACTION` with severity `WARNING`. Import with `expense_type=SETTLEMENT`. Do not compute participant shares for this row.

---

### Row 37 — Sam deposit share

```
description: Sam deposit share
paid_by: Sam
amount: 15000
split_type: equal
split_with: Aisha
notes: Sam moving in! paid Aisha his deposit
```

**Assessment:** This is a deposit payment from Sam to Aisha — not a shared household expense. The description and note confirm it is a transfer.

**Resolution strategy:** Flag as `SETTLEMENT_TRANSACTION` with severity `WARNING`. Import with `expense_type=SETTLEMENT`.

---

## 9. Refund Transaction (Negative Amount)

### Row 25 — Parasailing refund

```
description: Parasailing refund
paid_by: Dev
amount: -30
currency: USD
notes: one slot got cancelled
```

**Assessment:** Negative amount indicates a refund. The amount should be distributed back to participants. This is a legitimate entry but needs special handling — a refund reduces what participants owe.

**Resolution strategy:** Flag as `REFUND_TRANSACTION` with severity `INFO`. Import with `expense_type=REFUND`. Amount is stored as-is (negative). Share calculation applies the negative amount correctly.

---

## 10. Unknown / Guest Participant

### Row 22 — Parasailing

```
split_with: Aisha;Rohan;Priya;Dev;Dev's friend Kabir
notes: Kabir joined for the day
```

**Assessment:** "Dev's friend Kabir" is not a registered user. The name is informal and includes relationship context in the name itself.

**Resolution strategy:** Flag as `UNKNOWN_PARTICIPANT` with severity `WARNING`. Normalize the participant name to `Kabir` (strip "Dev's friend " prefix). Create a guest `User` record with `is_guest=True`. Anomaly record notes the name normalization.

---

## 11. Stale Participant (Moved-Out Member)

### Row 35 — Groceries BigBasket (02-04-2026)

```
split_with: Aisha;Rohan;Priya;Meera
notes: oops Meera still in the group list
```

**Assessment:** Meera moved out after 28-03-2026 (Row 32, farewell dinner). This expense dated 02-04-2026 still includes Meera. The note confirms this is an error.

**Resolution strategy:** Flag as `STALE_PARTICIPANT` with severity `WARNING`. Import with Meera listed in `split_with` as-is (preserving the raw data). Anomaly record notes that Meera moved out on approximately 2026-03-28. Do not remove Meera silently — flag for manual review.

---

## 12. Name Inconsistencies

### 12a. `priya` vs `Priya` (Row 8 vs all others)

```
Row 8: paid_by = "priya"
All others: "Priya"
```

**Resolution strategy:** Normalize to title case `Priya` during ingestion. Log transformation.

---

### 12b. `Priya S` vs `Priya` (Row 10)

```
Row 10: paid_by = "Priya S"
All others: "Priya"
```

**Assessment:** Could be the same Priya with an accidental last-name initial, or a different person. Given the group context (only one Priya is a participant), this is almost certainly the same person.

**Resolution strategy:** Flag as `NAME_INCONSISTENCY` with severity `WARNING`. Normalize to `Priya` and link to the existing user. Record the raw name in the anomaly.

---

### 12c. `rohan ` (trailing space) in Row 26

```
Row 26: paid_by = "rohan " (trailing space + lowercase)
```

**Resolution strategy:** Trim whitespace and normalize to title case → `Rohan`. Log transformation.

---

## 13. Conflicting Split Type vs Split Details

### Row 41 — Furniture for common room

```
split_type: equal
split_details: Aisha 1; Rohan 1; Priya 1; Sam 1
notes: split_type says equal but someone added shares anyway
```

**Assessment:** The `split_type` field says `equal` but `split_details` contain share-weight data (format identical to `share` type). These are contradictory: the note acknowledges the conflict. With 4 equal participants and 4 equal shares (1 each), the outcome is mathematically identical — so the split result is correct regardless of which type is used.

**Resolution strategy:** Flag as `CONFLICTING_SPLIT_INFO` with severity `WARNING`. Since the mathematical outcome is identical (all shares equal), import as `split_type=equal` and log the inconsistency. Clear the `split_details` to avoid confusion.

---

## 14. Percentage Split Not Summing to 100%

### Row 14 — Pizza Friday

```
split_type: percentage
split_details: Aisha 30%; Rohan 30%; Priya 30%; Meera 20%
notes: percentages might be off
```

**Assessment:** 30 + 30 + 30 + 20 = **110%**. The note acknowledges this. Over-allocated percentages mean participants are being overcharged.

**Resolution strategy:** Flag as `INVALID_PERCENTAGE_SPLIT` with severity `ERROR`. Do not silently normalize. Import with `status=WARNING` and anomaly record. Correct approach is to reject auto-normalization and surface for user review.

---

## 15. Multi-Currency Entries

Rows 19, 20, 22, 25 use `USD`; all others use `INR`. This is not an anomaly per se, but has implications:

- Cross-currency splits (e.g., Goa villa in USD, Goa flights in INR) should not be automatically summed
- No FX rate is available in the CSV

**Resolution strategy:** Store `currency` per expense. Do not perform cross-currency aggregation without explicit FX conversion (out of scope for this import). Flag in the import report as an informational note.

---

## 16. Participant Changes Over Time

The group composition changes throughout the CSV period:

| Period | Active Participants |
|---|---|
| Feb – Mar 28, 2026 | Aisha, Rohan, Priya, Meera |
| Mar 8–14, 2026 (Goa) | Aisha, Rohan, Priya, Dev |
| Apr 1 onwards | Aisha, Rohan, Priya, Sam |

This is **expected business logic**, not an anomaly — but the system must correctly track which users are participants per-expense rather than globally.

---

## Anomaly Registry (Machine-Readable Summary)

| Row | Category | Severity | Description |
|---|---|---|---|
| 4, 5 | `DUPLICATE_EXPENSE` | ERROR | Marina Bites dinner entered twice |
| 5 | `DUPLICATE_EXPENSE` | ERROR | Near-duplicate of Row 4 (rejected) |
| 6 | `AMOUNT_FORMAT_NORMALIZED` | INFO | Amount `"1,200"` → 1200 |
| 8 | `NAME_INCONSISTENCY` | INFO | `priya` → `Priya` |
| 9 | `AMOUNT_PRECISION_NORMALIZED` | INFO | `899.995` → `900.00` |
| 10 | `NAME_INCONSISTENCY` | WARNING | `Priya S` → `Priya` |
| 12 | `MISSING_PAYER` | ERROR | `paid_by` empty |
| 13 | `SETTLEMENT_TRANSACTION` | WARNING | Peer debt repayment |
| 14 | `INVALID_PERCENTAGE_SPLIT` | ERROR | Percentages sum to 110% |
| 22 | `UNKNOWN_PARTICIPANT` | WARNING | `Dev's friend Kabir` → guest user `Kabir` |
| 23, 24 | `DUPLICATE_EXPENSE` | ERROR | Thalassa dinner, conflicting payer/amount |
| 25 | `REFUND_TRANSACTION` | INFO | Negative amount refund |
| 26 | `AMBIGUOUS_DATE` | WARNING | `Mar-14` inferred as 2026-03-14 |
| 26 | `NAME_INCONSISTENCY` | INFO | `rohan ` (trailing space) → `Rohan` |
| 27 | `MISSING_CURRENCY` | ERROR | Currency blank, inferred INR |
| 30 | `ZERO_AMOUNT` | WARNING | Amount 0, note says duplicate fix |
| 33 | `AMBIGUOUS_DATE` | WARNING | `04-05-2026` — April 5 or May 4? |
| 35 | `STALE_PARTICIPANT` | WARNING | Meera listed post-move-out |
| 37 | `SETTLEMENT_TRANSACTION` | WARNING | Sam deposit to Aisha |
| 41 | `CONFLICTING_SPLIT_INFO` | WARNING | `split_type=equal` but has share details |
