def get_time_control_category(time_control: str) -> str:
    base_minutes, increment_seconds = parse_time_control(time_control)
    estimated_minutes = base_minutes + increment_seconds

    if estimated_minutes <= 10:
        return "blitz"
    if estimated_minutes < 60:
        return "rapid"
    return "standard"


def parse_time_control(time_control: str) -> tuple[int, int]:
    normalized = time_control.strip()
    if "+" in normalized:
        base_part, increment_part = normalized.split("+", 1)
    else:
        base_part, increment_part = normalized, "0"

    try:
        base_minutes = int(base_part.strip())
        increment_seconds = int(increment_part.strip())
    except ValueError:
        return (0, 0)

    return (max(base_minutes, 0), max(increment_seconds, 0))
