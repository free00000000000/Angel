import pandas as pd
import requests
import time
import os
from datetime import date
from tqdm import tqdm
from log import setup_logger

logger = setup_logger('crawler_logger', './data/log/crawler.log')
to_bot = setup_logger('bot', './data/log/to_bot.log')

def get_stock_price(start, end, stock_no):
  data = []
  for i in range(start, end+1):
    date = '2021%02d01' % (i)
    url = 'http://www.twse.com.tw/exchangeReport/STOCK_DAY?date={}&stockNo={}'.format(date, stock_no)
    r = requests.get(url)
    tmp = r.json()
    data.extend(tmp['data'])
    time.sleep(10)

  df = pd.DataFrame(data, columns=tmp['fields']).applymap(lambda x: x.replace(',', ''))
  df = df.drop(['漲跌價差'], axis=1)
  return df

def update_stock_price(stocks):
  logger.info("start")
  for stock_no in tqdm(stocks):
    try:
      filename = "./data/股價/{}.csv".format(stock_no)
      today = date.today()

      if os.path.isfile(filename):
        df = pd.read_csv(filename)
        y, m, d = [int(i) for i in df.iloc[-1]['日期'].split('/')]
        if today.day == d and today.month == m and today.year == y+1911:
          continue
        new = get_stock_price(m, today.month, stock_no)
        result = pd.concat([df, new])
        result.drop_duplicates(subset=['日期'], keep='last', inplace=True)
        result.to_csv(filename, index=False)
      
      else:
        new = get_stock_price(today.month-1, today.month, stock_no)
        new.to_csv(filename, index=False)
    except Exception as e:
      logger.error("{} |{}".format(e, stock_no))
  logger.info("End ")



def get_revenue(year, month, category='sii'):
  # category: sii/otc
  year -= 1911
  filename = "./data/月營收/{}_{}_{}.csv".format(year, month, category)
  if os.path.isfile(filename):  # 不更新營收
    print(filename, "ok")
    return False
  
  logger.info("New {}_{}_{} ".format(year, month, category))
  to_bot.info("New {}_{}_{} ".format(year, month, category))

  url = "https://mops.twse.com.tw/server-java/FileDownLoad"

  params = {
    "step": '9',
    "functionName": "show_file",
    "filePath": "/home/html/nas/t21/{}/".format(category),
    "fileName": "t21sc03_{}_{}.csv".format(year, month),
  }
  
  while True:
    try:
      html = requests.post(url, params)
      html.encoding = 'utf-8'

      data = html.text.replace('\r', '').split('\n')
      data = list(filter(None, data))

      df = []
      df.append(data[0].split(','))
      for d in data[1:]:
        df.append(list(eval(d)))
      df = pd.DataFrame(df)
      df.to_csv(filename, header=False, index=False)
      return True
    except Exception as e:
      logger.error(e)
      time.sleep(60)
  


if __name__ == '__main__':

  update_stock_price(1101)