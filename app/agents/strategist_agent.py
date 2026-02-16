from services.virality import score_event

POSTABLE_EMOTIONS = ["panic", "hype", "tension"]


def should_post(event, emotion):
    """
    Determine if we should post a tweet for the given event and emotion.
    Posts when virality score >= 50 or when emotion is one of panic/hype/tension.
    """
    if emotion in POSTABLE_EMOTIONS:
        return True

    score = score_event(event, emotion)
    if score >= 50:
        return True

    return False
