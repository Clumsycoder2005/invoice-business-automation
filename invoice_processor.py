from pathlib import Path
import csv
from decimal import Decimal, InvalidOperation

from invoice2data import extract_data


BASE_DIR = Path(__file__).parent
input_dir = BASE_DIR / "input"
output_dir = BASE_DIR / "output"


def to_decimal(value):
    """Convert a value to Decimal safely."""
    if value is None or value == "":
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def main():
    output_dir.mkdir(exist_ok=True)

    invoice_rows = []
    item_rows = []
    review_rows = []

    processed_count = 0
    failed_count = 0
    review_count = 0

    seen_invoice_numbers = set()

    pdf_files = list(input_dir.glob("*.pdf"))

    print(f"Found {len(pdf_files)} PDF invoice(s).")

    for pdf_file in pdf_files:
        print(f"\nProcessing: {pdf_file.name}")

        # =========================================================
        # 1. EXTRACT INVOICE
        # =========================================================

        try:
            invoice = extract_data(str(pdf_file))

        except Exception as error:
            failed_count += 1

            review_rows.append([
                pdf_file.name,
                "",
                "EXTRACTION_ERROR",
                str(error),
            ])

            print(f"FAILED: {pdf_file.name}")
            print(f"Reason: {error}")

            continue

        if not invoice:
            failed_count += 1

            review_rows.append([
                pdf_file.name,
                "",
                "NO_DATA",
                "Invoice extraction returned no data",
            ])

            print(f"FAILED: {pdf_file.name}")
            continue

        invoice_number = invoice.get("invoice_number")
        vendor = invoice.get("issuer")
        total = to_decimal(invoice.get("amount"))

        issues = []

        # =========================================================
        # 2. REQUIRED FIELD VALIDATION
        # =========================================================

        if not invoice_number:
            issues.append("Missing invoice number")

        if not vendor:
            issues.append("Missing vendor")

        if invoice.get("date") is None:
            issues.append("Missing invoice date")

        if total is None:
            issues.append("Missing or invalid invoice total")

        # =========================================================
        # 3. DUPLICATE DETECTION
        # =========================================================

        if invoice_number:
            if invoice_number in seen_invoice_numbers:
                issues.append("Duplicate invoice number")
            else:
                seen_invoice_numbers.add(invoice_number)

        # =========================================================
        # 4. PREPARE AND VALIDATE LINE ITEMS
        # =========================================================

        invoice_items = invoice.get("lines", [])

        item_total = Decimal("0")
        current_item_rows = []

        for item in invoice_items:

            quantity = to_decimal(item.get("qty"))
            unit_price = to_decimal(item.get("price_unit"))
            subtotal = to_decimal(item.get("price_subtotal"))

            product_name = item.get("name") or "Unknown product"

            # -----------------------------------------------------
            # Line-item validation
            # -----------------------------------------------------

            if quantity is None:
                issues.append(
                    f"LINE_ITEM_INVALID: {product_name} - invalid quantity"
                )

            if unit_price is None:
                issues.append(
                    f"LINE_ITEM_INVALID: {product_name} - invalid unit price"
                )

            if subtotal is None:
                issues.append(
                    f"LINE_ITEM_INVALID: {product_name} - invalid subtotal"
                )

            # -----------------------------------------------------
            # Quantity × unit price = subtotal
            # -----------------------------------------------------

            if (
                quantity is not None
                and unit_price is not None
                and subtotal is not None
            ):
                calculated_subtotal = quantity * unit_price

                difference = abs(calculated_subtotal - subtotal)

                if difference > Decimal("0.02"):
                    issues.append(
                        f"LINE_ITEM_MISMATCH: {product_name} "
                        f"expected={calculated_subtotal} "
                        f"actual={subtotal}"
                    )

            # -----------------------------------------------------
            # Add subtotal to invoice total calculation
            # -----------------------------------------------------

            if subtotal is not None:
                item_total += subtotal

            current_item_rows.append([
                invoice_number,
                product_name,
                item.get("qty"),
                item.get("price_unit"),
                item.get("line_tax_percent"),
                item.get("price_subtotal"),
            ])

        # =========================================================
        # 5. TOTAL RECONCILIATION
        # =========================================================

        if total is not None and invoice_items:

            difference = abs(total - item_total)

            if difference > Decimal("0.02"):
                issues.append(
                    f"TOTAL_MISMATCH: invoice={total}, "
                    f"line_items={item_total}, "
                    f"difference={difference}"
                )

        elif total is not None and not invoice_items:
            issues.append(
                "NO_LINE_ITEMS: no line items extracted"
            )

        # =========================================================
        # 6. ROUTE RESULT
        # =========================================================

        if issues:

            review_count += 1

            review_rows.append([
                pdf_file.name,
                invoice_number or "",
                " | ".join(issues),
                "REVIEW",
            ])

            print(f"REVIEW: {pdf_file.name}")
            print(f"Issues: {' | '.join(issues)}")

        else:

            # Only valid invoices reach the accepted datasets.

            invoice_rows.append([
                invoice_number,
                vendor,
                invoice.get("date"),
                invoice.get("amount"),
                invoice.get("amount_untaxed"),
                invoice.get("vat"),
                invoice.get("currency"),
                invoice.get("payment_method"),
            ])

            item_rows.extend(current_item_rows)

            processed_count += 1

            print(f"SUCCESS: {pdf_file.name}")

    # =============================================================
    # 7. WRITE INVOICES CSV
    # =============================================================

    with open(
        output_dir / "invoices.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "Invoice Number",
            "Vendor",
            "Date",
            "Total",
            "Untaxed Amount",
            "VAT",
            "Currency",
            "Payment Method",
        ])

        writer.writerows(invoice_rows)

    # =============================================================
    # 8. WRITE LINE ITEMS CSV
    # =============================================================

    with open(
        output_dir / "invoice_items.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "Invoice Number",
            "Product",
            "Quantity",
            "Unit Price",
            "Tax %",
            "Subtotal",
        ])

        writer.writerows(item_rows)

    # =============================================================
    # 9. WRITE REVIEW CSV
    # =============================================================

    with open(
        output_dir / "review.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "File",
            "Invoice Number",
            "Issue",
            "Status",
        ])

        writer.writerows(review_rows)

    # =============================================================
    # 10. FINAL REPORT
    # =============================================================

    print("\n" + "=" * 45)
    print("       INVOICE AUTOMATION REPORT")
    print("=" * 45)

    print(f"Files received:          {len(pdf_files)}")
    print(f"Successfully processed:  {processed_count}")
    print(f"Needs review:            {review_count}")
    print(f"Failed:                  {failed_count}")
    print(f"Invoices extracted:      {len(invoice_rows)}")
    print(f"Items extracted:         {len(item_rows)}")

    print("=" * 45)
    print("Output files:")
    print("  invoices.csv")
    print("  invoice_items.csv")
    print("  review.csv")
    print("=" * 45)


if __name__ == "__main__":
    main()