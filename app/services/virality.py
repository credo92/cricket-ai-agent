def score_event(event, emotion):
    score = 0

    if "WICKET" in event:
        score += 30

    if emotion in ["panic", "hype", "tension"]:
        score += 30

    if "last over" in event.lower():
        score += 40

    return score
