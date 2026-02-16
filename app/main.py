import logging
import os
import time
from datetime import datetime

from openai import RateLimitError
from config import MATCH_LOOP_SECONDS
from agents.watcher_agent import watch_match
from agents.narrative_agent import detect_narrative
from agents.strategist_agent import should_post
from agents.decision_agent import run_decision
from agents.engagement_agent import save_post
from x_client import post_tweet
from safety import human_delay, is_duplicate, remember_post
from openai_errors import handle_openai_rate_limit

def setup_logger():
    # Called once per main start. Log file path: logs/run_YYYYMMDD_HHMMSS.log
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"run_{now_str}.log")

    logger = logging.getLogger("main_logger")
    logger.setLevel(logging.INFO)
    # Remove all old handlers if called more than once
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    # Optional: also output to stdout (visible in docker/logs)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    logger.info("Logger initialized. Writing logs to %s", log_file)
    return logger

logger = None  # Will be set in __main__

def run_cycle():
    """V6: Simulate 3 candidates, predict engagement, post best, save predicted for learning."""
    global logger
    try:
        logger.info("Starting run_cycle")

        match_list = watch_match()
        if not match_list:
            logger.info("No matches to process, skipping cycle.")
            return

        for event, state in match_list:
            logger.info("Processing match: %s %s", event, state)
            print(event, state)

            emotion = detect_narrative(event, state)
            logger.info("Detected narrative/emotion: %s", emotion)

            if not should_post(event, emotion):
                logger.info("Should not post for this event-emotion, skipping.")
                continue

            # V6 Decision Intelligence: 3 candidates → predict engagement → choose best
            post, predicted_score = run_decision(event, emotion, num_candidates=3)
            logger.info("Decision made: post candidate '%s' with predicted score %s", post, predicted_score)

            if is_duplicate(post):
                logger.warning("Post is a duplicate, aborting: '%s'", post)
                continue

            logger.info("Waiting human delay before posting...")
            human_delay()

            post_id = post_tweet(post)
            logger.info("Posted tweet with id %s", post_id)

            remember_post(post)
            logger.info("Remembered post for duplicate checking.")

            save_post(post_id, post, emotion, emotion, predicted_score=predicted_score)
            logger.info("Saved post: %s (predicted score %s)", post, predicted_score)

            print("Posted (predicted score {}): {}".format(predicted_score, post))
            logger.info("Posted (predicted score {}): {}".format(predicted_score, post))
            # wait for 5 secconds
            print("Waiting for 5 Seconds")
            time.sleep(5)

    except Exception as e:
        logger.exception("Exception occurred in run_cycle: %s", e)
        raise


if __name__ == "__main__":
    # This block checks if the script was run with a command-line argument "feedback":
    import sys
    logger = setup_logger()

    logger.info("App started with args: %s", sys.argv)
    if len(sys.argv) > 1 and sys.argv[1] == "feedback":
        # If argument is "feedback", import and execute the learning job to backfill actual engagement.
        try:
            logger.info("Running feedback cycle...")
            from services.feedback_learning import run_feedback_cycle
            n = run_feedback_cycle()  # Run the feedback learning cycle, which updates posts with real engagement
            logger.info("Updated engagement for %d posts", n)
            print("Updated engagement for {} posts".format(n))  # Output how many posts were updated
        except RateLimitError as e:
            # If the OpenAI API rate limit is hit, handle it with a custom error handler.
            logger.error("OpenAI RateLimitError: %s", e)
            handle_openai_rate_limit(e)
        except Exception as e:
            logger.exception("Exception in feedback mode: %s", e)
            raise
    else:
        logger.info("Starting main cron-loop (infinite mode)")
        while True:
            try:
                run_cycle()
                time.sleep(MATCH_LOOP_SECONDS)
            except RateLimitError as e:
                logger.error("OpenAI RateLimitError: %s", e)
                handle_openai_rate_limit(e)
            except Exception as e:
                logger.exception("Unhandled exception in main loop: %s", e)