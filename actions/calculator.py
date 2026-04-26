"""calculator.py — Math, unit conversions, currency"""
import math, json, threading


def calculator(parameters: dict, player=None) -> str:
    expr       = parameters.get("expression", "")
    show_steps = parameters.get("show_steps", False)

    if not expr:
        return "No expression provided."

    # Safe eval context
    safe_globals = {
        "__builtins__": {},
        "math": math, "sqrt": math.sqrt, "pi": math.pi, "e": math.e,
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "log": math.log, "log10": math.log10, "floor": math.floor,
        "ceil": math.ceil, "abs": abs, "round": round, "pow": pow,
    }

    try:
        # Clean expression
        clean = expr.replace("^", "**").replace("×", "*").replace("÷", "/")
        result = eval(clean, safe_globals)
        answer = f"{expr} = {result}"

        if show_steps and player and hasattr(player, "anim"):
            steps = [
                {"step": "1", "description": f"Expression: {expr}"},
                {"step": "2", "description": f"Simplified: {clean}"},
                {"step": "3", "description": f"Result: {result}"},
            ]
            def _show():
                player.anim.show(
                    anim_type="steps",
                    title="Calculation",
                    content=json.dumps(steps),
                    color="#00d4ff",
                    duration=8,
                )
            threading.Thread(target=_show, daemon=True).start()

        return answer

    except Exception as e:
        # Try unit conversions
        return _unit_convert(expr) or f"Could not evaluate: {expr}. Error: {e}"


def _unit_convert(expr: str) -> str:
    conversions = {
        ("km", "miles"):  lambda x: x * 0.621371,
        ("miles", "km"):  lambda x: x * 1.60934,
        ("kg", "lbs"):    lambda x: x * 2.20462,
        ("lbs", "kg"):    lambda x: x * 0.453592,
        ("celsius", "fahrenheit"): lambda x: x * 9/5 + 32,
        ("fahrenheit", "celsius"): lambda x: (x - 32) * 5/9,
        ("meters", "feet"): lambda x: x * 3.28084,
        ("feet", "meters"): lambda x: x * 0.3048,
        ("liters", "gallons"): lambda x: x * 0.264172,
        ("gallons", "liters"): lambda x: x * 3.78541,
    }
    e = expr.lower()
    for (src, tgt), fn in conversions.items():
        if src in e and ("to" in e or tgt in e):
            import re
            nums = re.findall(r"[\d.]+", e)
            if nums:
                val    = float(nums[0])
                result = fn(val)
                return f"{val} {src} = {result:.4f} {tgt}"
    return ""
