"""
process_leads.py
----------------
Reads leads_raw.csv, applies exclusion rules, writes send_ready.csv,
and prints a QA report to stdout.

Exclusion rules (first match wins, checked in order):
  1. email is missing or blank
  2. first_name is missing or blank
  3. email domain is in the suppression list
  4. employees is blank / non-numeric / < 250 / > 10 000
  5. email local-part contains a generic-inbox keyword
  6. email domain is a free consumer provider (gmail, yahoo, hotmail, outlook)
  7. title does not contain an ICP keyword
  8. duplicate email address (case-insensitive), keep first occurrence

Warnings (row passes, but flagged in QA report):
  W1. email domain does not match company_domain
"""

import csv
import sys

INPUT_FILE  = "leads_raw.csv"
OUTPUT_FILE = "send_ready.csv"

SUPPRESSED_DOMAINS  = {"ridgeline3pl.com", "norvind.com", "bellwether-scm.com"}
FREE_EMAIL_DOMAINS  = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com"}
GENERIC_WORDS       = {"info", "contact", "warehouse", "enquiries", "general", "admin", "hello"}
ICP_KEYWORDS        = {"vp", "director", "head", "coo", "owner"}

EXCLUSION_REASONS = [
    "missing_email",
    "missing_first_name",
    "suppressed_domain",
    "invalid_employees",
    "generic_email",
    "free_email_domain",
    "title_not_icp",
    "duplicate_email",
]

REASON_LABELS = {
    "missing_email":     "Email missing or blank",
    "missing_first_name":"First name missing or blank",
    "suppressed_domain": "Email domain in suppression list",
    "invalid_employees": "Employees blank / non-numeric / out of range (250–10 000)",
    "generic_email":     "Generic inbox email",
    "free_email_domain": "Free consumer email provider (gmail / yahoo / hotmail / outlook)",
    "title_not_icp":     "Title does not match ICP",
    "duplicate_email":   "Duplicate email address (case-insensitive), kept first occurrence",
}

def exclusion_reason(row: dict, seen_emails: set) -> str | None:
    email      = row.get("email",      "").strip()
    first_name = row.get("first_name", "").strip()
    title      = row.get("title",      "").strip()
    emp_raw    = row.get("employees",  "").strip()

    if not email:
        return "missing_email"
    if not first_name:
        return "missing_first_name"

    domain = email.rsplit("@", 1)[1].lower() if "@" in email else ""

    if domain in SUPPRESSED_DOMAINS:
        return "suppressed_domain"

    if not emp_raw:
        return "invalid_employees"
    try:
        employees = float(emp_raw)
    except ValueError:
        return "invalid_employees"
    if employees < 250 or employees > 10_000:
        return "invalid_employees"

    local_part = email.rsplit("@", 1)[0].lower() if "@" in email else email.lower()
    for word in GENERIC_WORDS:
        if word in local_part:
            return "generic_email"

    if domain in FREE_EMAIL_DOMAINS:
        return "free_email_domain"

    title_lower = title.lower()
    if not any(kw in title_lower for kw in ICP_KEYWORDS):
        return "title_not_icp"

    email_key = email.lower()
    if email_key in seen_emails:
        return "duplicate_email"
    seen_emails.add(email_key)

    return None

def domain_mismatch_warning(row: dict) -> str | None:
    email          = row.get("email",          "").strip()
    company_domain = row.get("company_domain", "").strip().lower()
    if not email or not company_domain or "@" not in email:
        return None
    email_domain = email.rsplit("@", 1)[1].lower()
    if email_domain != company_domain:
        name = f"{row.get('first_name','').strip()} {row.get('last_name','').strip()}".strip()
        return (
            f"  ⚠  {name} ({row.get('company','').strip()}) — "
            f"email @{email_domain} ≠ company_domain {company_domain}"
        )
    return None

def main() -> None:
    exclusion_counts: dict[str, int] = {r: 0 for r in EXCLUSION_REASONS}
    rows_in:   list[dict] = []
    rows_out:  list[dict] = []
    warnings:  list[str]  = []
    fieldnames: list[str] = []
    seen_emails: set[str] = set()

    try:
        with open(INPUT_FILE, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None:
                print("ERROR: Input file is empty or has no header row.", file=sys.stderr)
                sys.exit(1)
            fieldnames = list(reader.fieldnames)
            for row in reader:
                rows_in.append(row)
                reason = exclusion_reason(row, seen_emails)
                if reason:
                    exclusion_counts[reason] += 1
                else:
                    rows_out.append(row)
                    w = domain_mismatch_warning(row)
                    if w:
                        warnings.append(w)
    except FileNotFoundError:
        print(f"ERROR: Cannot find input file '{INPUT_FILE}'.", file=sys.stderr)
        sys.exit(1)

    total_in       = len(rows_in)
    total_out      = len(rows_out)
    total_excluded = sum(exclusion_counts.values())

    if total_out + total_excluded != total_in:
        print(
            f"ERROR: Reconciliation failed — "
            f"{total_out} (output) + {total_excluded} (excluded) = "
            f"{total_out + total_excluded}, expected {total_in}.",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=fieldnames,
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        writer.writerows(rows_out)

    sep = "─" * 60
    print(sep)
    print("  LEADS PROCESSING — QA REPORT")
    print(sep)
    print(f"  Input file   : {INPUT_FILE}")
    print(f"  Output file  : {OUTPUT_FILE}")
    print(sep)
    print(f"  Total input rows   : {total_in:>4}")
    print(f"  Total output rows  : {total_out:>4}")
    print(f"  Total excluded     : {total_excluded:>4}")
    print(sep)
    print("  Exclusions by reason:")
    for reason in EXCLUSION_REASONS:
        count = exclusion_counts[reason]
        label = REASON_LABELS[reason]
        marker = "  " if count == 0 else "! "
        print(f"    {marker}{count:>2}  {label}")
    print(sep)
    reconciliation_sum = total_out + total_excluded
    print(
        f"  Reconciliation : {total_out} + {total_excluded} = {reconciliation_sum}"
        f"  (expected {total_in})"
    )
    if reconciliation_sum == total_in:
        print("  Result         : OK ✓")
    else:
        print("  Result         : FAILED ✗")
    print(sep)
    if warnings:
        print("  Warnings — rows included but need review:")
        for w in warnings:
            print(w)
        print(sep)

if __name__ == "__main__":
    main()
