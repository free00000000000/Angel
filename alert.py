from logging import log
import pandas as pd
from log import setup_logger


logger = setup_logger('alert_logger', './data/log/alert.log')
# 五均向上突破十均

class Stock:
  def __init__(self, stock, date) -> None:
    self.price = pd.read_csv('data/股價/{}.csv'.format(stock), index_col=['日期'])
    self.price = self.price.loc[:date]
    self.stock = stock
    self.open = self.price['開盤價'].astype(float)
    self.high = self.price['最高價'].astype(float)
    self.low = self.price['最低價'].astype(float)
    self.close = self.price['收盤價'].astype(float)
    self.volume = self.price['成交股數'].astype(float) // 1000

  def low_price(self):
    if self.close[-1] < self.close[-10:].min()*1.15:
      logger.info("|{}".format(self.stock))
      return True
    return False 

  def large_volume(self):
    if self.volume[-2]*2 <= self.volume[-1]:
      logger.info("|{}".format(self.stock))
      return True
    return False

  def long_red(self):
    if self.close[-1]>=self.open[-1]*1.03:
      logger.info("|{}".format(self.stock))
      return True
    return False

  def long_black(self):
    if self.close[-1] < self.open[-1]*0.97:
      logger.info("|{}".format(self.stock))
      return True
    return False

  def up(self, percent):
    p = 1 + percent/100
    if self.close[-1] >= self.close[-2]*p:
      logger.info("{}% |{}".format(percent, self.stock))
      return True
    return False


  def up_MA(self, days, ma):
    if sum(self.close[-days:] >= self.MA(ma)) == days:
      logger.info("連{}日上{}均 |{}".format(days, ma, self.stock))
      return True
    return False

  # def min_volume(self, days):
  #   return self.volume[-days:].min() > 500
  
  # def down_MA(self, days, ma):
  #   return sum(self.price.iloc[-days:]['收盤價'] < self.MA(ma)) == days

  def MA(self, n):
    return self.close[-n:].mean()

def show_alert(year, month, day):
  year = year-1911 if year > 1911 else year
  date = "{}/{:02d}/{:02d}".format(year, month, day)
  msg = [date+'：']
  df = pd.read_csv('./data/file/record.csv')
  df = df[df['buy_date']==date]
  for row in df.iterrows():
    # print(row[1]['stock'], row[1]['buy_comment'])
    m = "買入 {} ({})".format(row[1]['stock'], row[1]['buy_comment'])
    msg.append(m)
  # msg.append('-'*25)
  
  # print('\n'.join(msg))
  # TODO:
  # 買進/賣出訊號
  # 技術面訊號
  # 基本面訊號

  return '\n'.join(msg)

if __name__ == '__main__':
  # s = Stock(1101, '110/01/11')
  # s.up_MA(3, 5)
  show_alert(2021, 7, 7)
  pass