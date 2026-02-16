def detect_narrative(event, state):
    if "WICKET" in event and state["required_rr"] > 10:
        return "panic"

    if "six" in event.lower():
        return "hype"

    if state["overs_left"] < 3:
        return "tension"

    return "neutral"
