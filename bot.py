from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram.ext import MessageHandler, Filters
from datetime import date
import subprocess
import json

from group import Group
from alert import show_alert
from log import setup_logger

logger = setup_logger('angel_logger', './data/log/angel.log')
filename = 'data/log/to_bot.log'


with open('data/file/parm.json') as jf:
  parm = json.load(jf)

TOKEN = parm['token']
updater = Updater(token=TOKEN, use_context=True)

def vaild_id(id):
  return id in parm['vaild_id']

def start(update, context):
  logger.warning(update.effective_chat.id)
  context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

def get_rev_highlight(update, context):
  if not vaild_id(update.effective_chat.id): return
  try: 
    year = int(context.args[0])
    month = int(context.args[1])
  except:
    context.bot.send_message(chat_id=update.effective_chat.id, text="輸入錯誤！\n正確格式: /rev 年 月")
    return

  g = Group()
  msg = g.revenue_highlight(year, month)
  context.bot.send_message(chat_id=update.effective_chat.id, text=msg)


def send_alert(context: CallbackContext):
  today = date.today()
  t = today.isoformat()
  line = subprocess.check_output(['tail', '-1', 'data/log/angel.log']).decode().split(' ')
  if len(line)>4 and line[1]==t and line[0]=='INFO' and line[3]=='send_alert' and line[4]=='End': return

  line = subprocess.check_output(['tail', '-1', filename]).decode().split(' ')
  if len(line)>4 and line[1]==t and line[0]=='INFO' and line[3]=='check_sell' and line[4]=='End':
    tmp = subprocess.check_output(['head', '-n-1', filename]).decode()
    with open(filename, 'w') as f: 
      f.write(tmp)

    msg = show_alert(today.year, today.month, today.day)
    for i in parm['vaild_id']:
      context.bot.send_message(chat_id=i, text=msg)
    logger.info("End ")

def send_rev_highlight(context: CallbackContext):
  today = date.today()
  t = today.isoformat()
  line = subprocess.check_output(['tail', '-1', filename]).decode().split(' ')
  if len(line)>5 and line[1]==t and line[0]=='INFO' and line[3]=='get_revenue' and line[4]=='New':
    tmp = subprocess.check_output(['head', '-n-1', filename]).decode()
    with open(filename, 'w') as f: 
      f.write(tmp)
    y, m, c = line[5].split('_')
    g = Group()
    msg = g.revenue_highlight(int(y), int(m))
    for i in parm['vaild_id']:
      context.bot.send_message(chat_id=i, text=msg)
    logger.info("End ")


dispatcher = updater.dispatcher

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

dispatcher.add_handler(CommandHandler('rev', get_rev_highlight))

job = updater.job_queue
# job_alert = job.run_repeating(send_alert, interval=5, first=0)
job_alert = job.run_repeating(send_alert, interval=3600, first=0)
job_alert = job.run_repeating(send_rev_highlight, interval=3600, first=1800)

updater.start_polling()
updater.idle()