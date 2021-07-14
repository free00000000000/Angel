from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram.ext import MessageHandler, Filters
from datetime import date
import subprocess
import json
import os

from telegram.files.document import Document

from group import Group
# from alert import show_alert
from log import setup_logger
import logging

logger = setup_logger('angel_logger', './data/log/angel.log')
filename = 'data/log/to_bot.log'
# to_bot = setup_logger('bot', filename)
to_bot = logging.getLogger('bot')



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
  
    # for i in [548701539]:
  context.bot.send_document(chat_id=update.effective_chat.id, document=open("data/file/rev_highlight_sii.csv", 'rb'))

def get_alert(update, context):
  # get alert with revenue
  if not vaild_id(update.effective_chat.id): return
  try: 
    year = int(context.args[0])
    month = int(context.args[1])
    day = int(context.args[2])
  except:
    context.bot.send_message(chat_id=update.effective_chat.id, text="輸入錯誤！\n正確格式: /alert 年 月 日")
    return

  g = Group()
  g.show_alert(year, month, day)
  g.read_alert_and_rev()
  context.bot.send_document(chat_id=update.effective_chat.id, document=open("data/file/rev_alert_sii.csv", 'rb'), filename="alert_{}_{}_{}.csv".format(year, month, day))


def send_alert(context: CallbackContext):
  logger.info("Start ")
  today = date.today()
  t = today.isoformat()

  line = subprocess.check_output(['tail', '-1', filename]).decode().split(' ')
  if len(line)>4 and line[1]==t and line[0]=='INFO' and line[3]=='show_alert' and line[4]=='End':
    to_bot.info("Start ")

    g = Group()
    # g.show_alert(today.year, today.month, today.day)
    msg = g.read_alert_and_rev()
    
    os.system("cp data/file/rev_alert_sii.csv data/alert/alert_{}_{}_{}.csv".format(today.year, today.month, today.day))

    for i in parm['vaild_id']:
      context.bot.send_message(chat_id=i, text=msg)
      context.bot.send_document(chat_id=i, document=open("data/file/rev_alert_sii.csv", 'rb'), filename="alert_{}_{}_{}.csv".format(today.year, today.month, today.day))
    logger.info("End ")

def send_rev_highlight(context: CallbackContext):
  logger.info("Start ")
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

dispatcher.add_handler(CommandHandler('start', start))
# dispatcher.add_handler(CommandHandler('rev', get_rev_highlight))
dispatcher.add_handler(CommandHandler('alert', get_alert))

job = updater.job_queue
# job_alert = job.run_repeating(send_alert, interval=5, first=0)
job_alert = job.run_repeating(send_alert, interval=1800, first=1750)
job_alert = job.run_repeating(send_rev_highlight, interval=1800, first=0)

updater.start_polling()
updater.idle()