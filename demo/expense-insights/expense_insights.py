# SPDX-FileCopyrightText: 2026 Leonardo Muffato (AUTOSOFT Engineering - www.autosoft-engineering.de)
# SPDX-License-Identifier: MIT

"""Small, intentionally concentrated expense-reporting demo application."""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True)
class Transaction:
    booked_on: date
    description: str
    amount: Decimal
    category: str = "Other"


CATEGORY_RULES = {
    "Groceries": ("market", "grocery", "fresh foods"),
    "Mobility": ("rail", "fuel", "transit"),
    "Housing": ("rent", "energy", "internet"),
    "Income": ("salary", "refund"),
}


def load_transactions(path: Path) -> list[Transaction]:
    transactions: list[Transaction] = []
    with path.open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            transactions.append(
                Transaction(
                    booked_on=date.fromisoformat(row["date"]),
                    description=row["description"],
                    amount=Decimal(row["amount"]),
                )
            )
    return transactions


def categorize(transaction: Transaction) -> Transaction:
    normalized = re.sub(r"\s+", " ", transaction.description.casefold()).strip()
    for category, matchers in CATEGORY_RULES.items():
        if any(matcher in normalized for matcher in matchers):
            return Transaction(
                booked_on=transaction.booked_on,
                description=transaction.description,
                amount=transaction.amount,
                category=category,
            )
    return transaction


def summarize(transactions: list[Transaction]) -> dict[str, Decimal]:
    totals: defaultdict[str, Decimal] = defaultdict(Decimal)
    for transaction in transactions:
        totals[transaction.category] += transaction.amount
    return dict(sorted(totals.items()))


def render_report(totals: dict[str, Decimal]) -> str:
    heading = "Monthly expense summary"
    lines = [heading, "=" * len(heading)]
    lines.extend(f"{category:12} {amount:>10.2f}" for category, amount in totals.items())
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize a transaction CSV file.")
    parser.add_argument("transactions", type=Path)
    arguments = parser.parse_args()

    transactions = [categorize(item) for item in load_transactions(arguments.transactions)]
    print(render_report(summarize(transactions)))


if __name__ == "__main__":
    main()
