export const SAMPLES = {
  quickcalc: {
    id: 'quickcalc',
    name: 'QuickCalc',
    appName: 'QuickCalc',
    code: `"""PyForge Demo — QuickCalc

A small menu-driven calculator (stdlib only).
"""

import sys


def add(a: float, b: float) -> float:
    return a + b


def subtract(a: float, b: float) -> float:
    return a - b


def multiply(a: float, b: float) -> float:
    return a * b


def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


OPERATIONS = {
    "1": ("Add", add),
    "2": ("Subtract", subtract),
    "3": ("Multiply", multiply),
    "4": ("Divide", divide),
}


def read_number(prompt: str) -> float:
    while True:
        raw = input(prompt).strip()
        try:
            return float(raw)
        except ValueError:
            print("  Please enter a valid number.")


def run_interactive() -> None:
    print("=" * 40)
    print("  QuickCalc — PyForge Demo App")
    print("=" * 40)
    for key, (label, _) in OPERATIONS.items():
        print(f"  {key}. {label}")
    print("  q. Quit")
    print()

    choice = input("Choose operation: ").strip().lower()
    if choice in ("q", "quit", "exit"):
        print("Goodbye!")
        return

    if choice not in OPERATIONS:
        print("Invalid choice.")
        return

    label, func = OPERATIONS[choice]
    a = read_number("First number: ")
    b = read_number("Second number: ")
    try:
        result = func(a, b)
    except ValueError as exc:
        print(f"Error: {exc}")
        return

    print(f"\\nResult: {a} {label.lower()} {b} = {result}\\n")


def main() -> None:
    run_interactive()


if __name__ == "__main__":
    main()
`,
  },
  tip_calculator: {
    id: 'tip_calculator',
    name: 'Tip Calculator',
    appName: 'TipCalc',
    code: `"""PyForge Demo — Tip Calculator"""

def calculate_bill(total: float, tip_percent: float, people: int) -> None:
    if total <= 0 or people < 1:
        print("Invalid total or party size.")
        return
    tip = total * (tip_percent / 100)
    grand = total + tip
    per_person = grand / people
    print(f"\\nBill:      ${total:.2f}")
    print(f"Tip ({tip_percent}%): ${tip:.2f}")
    print(f"Total:     ${grand:.2f}")
    print(f"Per person ({people}): ${per_person:.2f}\\n")


def main() -> None:
    print("=== Tip Calculator (PyForge Demo) ===")
    try:
        total = float(input("Bill amount ($): "))
        tip_pct = float(input("Tip percent (e.g. 18): "))
        people = int(input("Split between how many people? "))
    except ValueError:
        print("Please enter valid numbers.")
        return
    calculate_bill(total, tip_pct, people)


if __name__ == "__main__":
    main()
`,
  },
};

export const DEFAULT_SAMPLE = SAMPLES.quickcalc;
