from apscheduler.schedulers.blocking import BlockingScheduler
from main import run_cycle
from services.feedback_learning import run_feedback_cycle

scheduler = BlockingScheduler()

scheduler.add_job(run_cycle, "interval", seconds=30)
# V6: learn from misses — backfill actual engagement every 15 min
scheduler.add_job(run_feedback_cycle, "interval", minutes=15)

scheduler.start()
