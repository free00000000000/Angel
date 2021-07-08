from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram.ext import MessageHandler, Filters
from datetime import date
import subprocess
import json

from alert import show_alert
from log import setup_logger
logger = setup_logger('angel_logger', './data/log/angel.log')

with open('data/file/parm.json') as jf:
  parm = json.load(jf)

TOKEN = parm['token']
updater = Updater(token=TOKEN, use_context=True)

def start(update, context):
  logger.warning(update.effective_chat.id)
  context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

def caps(update, context):
    text_caps = ' '.join(context.args).upper()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)

def echo(update, context):
  text = update.message.text
  print(update.effective_chat.id)
  context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def send_alert(context: CallbackContext):
  today = date.today()
  t = today.isoformat()
  line = subprocess.check_output(['tail', '-1', 'data/log/angel.log']).decode().split(' ')
  if len(line)>4 and line[1]==t and line[0]=='INFO' and line[3]=='send_alert' and line[4]=='End': return

  line = subprocess.check_output(['tail', '-1', 'data/log/group.log']).decode().split(' ')
  if len(line)>4 and line[1]==t and line[0]=='INFO' and line[3]=='check_sell' and line[4]=='End':
    msg = show_alert(today.year, today.month, today.day)
    for i in parm['vaild_id']:
      context.bot.send_message(chat_id=i, text=msg)
    logger.info("End ")



dispatcher = updater.dispatcher

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

# caps_handler = CommandHandler('caps', caps)
# dispatcher.add_handler(caps_handler)

# echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
# dispatcher.add_handler(echo_handler)

job = updater.job_queue
# job_alert = job.run_repeating(send_alert, interval=5, first=0)
job_alert = job.run_repeating(send_alert, interval=3600, first=0)

updater.start_polling()
updater.idle()