from apscheduler.schedulers.blocking import BlockingScheduler 
import logging 
from main import update
from log import setup_logger

logger = setup_logger('apscheduler.executors.default', './data/log/schedule.log')


sched = BlockingScheduler()

sched.add_job(update, 'cron', hour='18') 
# sched.add_job(get_AQI, 'interval', seconds=10) 

print('before the start funciton') 
sched.start() 