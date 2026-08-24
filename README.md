# Invoice Business Automation

A Python-based invoice processing automation pipeline that extracts structured invoice data from PDF files, validates the extracted information, detects duplicate invoices, reconciles line-item totals, and routes problematic invoices for manual review.

This project uses the open-source `invoice2data` library as the invoice extraction engine and adds a custom validation and processing layer around it.

## Overview

Manual invoice processing often involves repeatedly copying information from PDF invoices into spreadsheets or accounting systems.

This project automates that workflow:

```text
PDF invoices
     |
     v
invoice2data extraction
     |
     v
Structured invoice data
     |
     +-- Required-field validation
     +-- Duplicate detection
     +-- Line-item validation
     +-- Total reconciliation
     |
     v
Accepted invoices -----> invoices.csv
Line items ------------> invoice_items.csv
Problems / duplicates -> review.csv
```

The goal is not simply to extract data, but to validate the extracted data before accepting it.

## Features

### Invoice extraction

Extracts key invoice information from PDF files using `invoice2data`, including:

* Invoice number
* Vendor
* Invoice date
* Total amount
* Untaxed amount
* VAT
* Currency
* Payment method

### Required-field validation

The processor checks whether important invoice fields were successfully extracted.

Invoices with missing critical information are routed to the review dataset instead of being silently accepted.

### Duplicate detection

The processor keeps track of invoice numbers during a processing run.

If the same invoice number appears again, it is flagged as:

```text
Duplicate invoice number
```

This helps prevent the same invoice from being accidentally processed as a new record.

### Line-item validation

For each extracted line item, the processor validates:

* Quantity
* Unit price
* Subtotal

It also checks:

```text
quantity x unit price = subtotal
```

A tolerance of `0.02` is used to account for minor rounding differences.

### Total reconciliation

The processor compares the sum of extracted line-item subtotals against the invoice total.

Large discrepancies are flagged for review.

### Review workflow

Invoices containing validation problems are not included in the accepted invoice dataset.

Instead, they are written to:

```text
output/review.csv
```

This creates a simple human-in-the-loop workflow:

```text
Valid invoice
     |
     v
Accepted dataset

Problematic invoice
     |
     v
Review queue
     |
     v
Manual verification
```

## Output

The processor generates three CSV files.

### `invoices.csv`

Contains accepted invoice-level records.

Example:

```text
Invoice Number,Vendor,Date,Total,Currency
993548900,Coolblue B.V.,2014-04-19 00:00:00,717.97,EUR
```

### `invoice_items.csv`

Contains extracted line items.

Example:

```text
Invoice Number,Product,Quantity,Unit Price,Tax %,Subtotal
993548900,Apple iPad Air Wifi 16 GB Zilver,1,399.0,21,399.0
993548900,Nintendo 3DS XL Wit + Blauw,1,189.0,21,189.0
```

### `review.csv`

Contains invoices that require manual verification.

Example:

```text
File,Invoice Number,Issue,Status
coolblue1_copy.pdf,993548900,Duplicate invoice number,REVIEW
```

## Example Run

A test run with two PDFs demonstrates the duplicate-detection workflow:

```text
Found 2 PDF invoice(s).

Processing: coolblue1.pdf
SUCCESS: coolblue1.pdf

Processing: coolblue1_copy.pdf
REVIEW: coolblue1_copy.pdf
Issues: Duplicate invoice number

=============================================
       INVOICE AUTOMATION REPORT
=============================================
Files received:          2
Successfully processed:  1
Needs review:            1
Failed:                  0
Invoices extracted:      1
Items extracted:         5
=============================================
Output files:
  invoices.csv
  invoice_items.csv
  review.csv
```

The first invoice is accepted, while the duplicate invoice is automatically routed to the review dataset.

## Project Structure

```text
invoice2data/
|
+-- invoice_processor.py
|       Custom invoice automation and validation pipeline
|
+-- tests/
|       +-- test_invoice_processor.py
|       +-- Existing invoice2data test suite
|
+-- input/
|       Local PDF test invoices
|
+-- output/
|       +-- invoices.csv
|       +-- invoice_items.csv
|       +-- review.csv
|
+-- src/
|       invoice2data extraction library
|
+-- README.md
```

The `input/` and `output/` directories are excluded from Git because they contain local test data and generated files.

## Installation

This project requires Python 3.10 or newer.

Install the project dependencies using the project's existing Python environment.

If `pytest` is not already installed, install it with:

```powershell
python -m pip install pytest
```

## Running the Automation

Place PDF invoices inside:

```text
input/
```

Then run:

```powershell
python invoice_processor.py
```

The processor writes the results to:

```text
output/invoices.csv
output/invoice_items.csv
output/review.csv
```

## Running the Tests

Run the custom invoice-processor tests with:

```powershell
python -m pytest tests/test_invoice_processor.py -v
```

The current custom test suite verifies the safe decimal-conversion utility used by the validation pipeline.

Example:

```text
5 passed
```

The repository also contains the broader test suite belonging to the underlying `invoice2data` project.

## Technologies

* Python
* invoice2data
* CSV
* Decimal
* pathlib
* pytest
* Git
* GitHub

## Validation Logic

The processing pipeline follows this decision process:

```text
Extract invoice
      |
      v
Extraction successful?
   +--+--+
   |     |
  No    Yes
   |     |
   v     v
Review  Validate fields
          |
          v
      Duplicate?
       +--+--+
       |     |
      Yes    No
       |     |
       v     v
     Review  Validate line items
                  |
                  v
             Reconcile totals
                  |
             +----+----+
             |         |
          Problems   Valid
             |         |
             v         v
           Review    Accept
```

This approach reduces the risk of silently writing incorrect extracted data into downstream business records.

## Limitations

This is a portfolio/business-automation project rather than a production accounting system.

Current limitations include:

* PDF extraction quality depends on the underlying invoice template and extraction backend.
* Different invoice layouts may require additional `invoice2data` templates.
* OCR-based invoices may require additional configuration.
* The current duplicate detection operates within a single processing run.
* CSV files are used as the output layer rather than a database or accounting-system integration.
* Human review is required for flagged invoices.

## Future Production Extensions

Potential production extensions could include:

* Database storage
* Cloud storage integration
* Email attachment processing
* Accounting-system/API integration
* Persistent duplicate detection
* Structured logging
* Automated monitoring
* Web dashboard
* Authentication and user management

These are intentionally outside the current project scope.

## What This Project Demonstrates

This project demonstrates practical automation concepts beyond simply writing a PDF parser:

* Working with an existing Python library
* File-system automation
* Structured data extraction
* Data validation
* Financial calculations using `Decimal`
* Duplicate detection
* Error handling
* Human-in-the-loop review workflows
* CSV generation
* Automated testing
* Git/GitHub project management

## Attribution

The invoice extraction functionality is provided by the open-source `invoice2data` project:

https://github.com/invoice-x/invoice2data

This repository adds the custom `invoice_processor.py` automation and validation workflow around that extraction functionality.
