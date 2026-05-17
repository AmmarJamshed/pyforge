"""PyForge Demo — QuickCalc

A small menu-driven calculator (stdlib only).
Good test for: Desktop EXE, Linux binary, Android APK.

Suggested app name: QuickCalc
Suggested target: desktop_windows
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

    print(f"\nResult: {a} {label.lower()} {b} = {result}\n")


def run_cli() -> None:
    """One-shot mode: python quickcalc.py add 10 3"""
    if len(sys.argv) < 4:
        print("Usage: quickcalc.py <add|sub|mul|div> <a> <b>")
        sys.exit(1)
    op_map = {"add": add, "sub": subtract, "mul": multiply, "div": divide}
    op = sys.argv[1].lower()
    if op not in op_map:
        print(f"Unknown op: {op}")
        sys.exit(1)
    a, b = float(sys.argv[2]), float(sys.argv[3])
    print(op_map[op](a, b))


def main() -> None:
    if len(sys.argv) > 1:
        run_cli()
    else:
        run_interactive()


if __name__ == "__main__":
    main()
