import logging
import pandas as pd
from revenue import get_target, by_stock, get_volume
from alert import Stock
from log import setup_logger

logger = setup_logger('group_logger', './data/log/group.log')

class Group:
  def __init__(self) -> None:
    self.group_file = './data/file/group.csv'
    self.record_file = './data/file/record.csv'
    self.result_file = './data/file/result.csv'
    self.stocks = pd.read_csv(self.group_file, index_col='stock')
    self.record = pd.read_csv(self.record_file, index_col='stock')
    self.result = pd.read_csv(self.result_file, index_col='stock')

  
  def update(self, rev_year, rev_month):
    # rev_year: 西元
    target = get_target(rev_year, rev_month, 'sii')
    self.stocks = self.stocks.append(pd.DataFrame(index=target))
    self.stocks = self.stocks[~self.stocks.index.duplicated(keep='first')]
    self.stocks['increase'] = self.stocks.index.isin(target).astype(int)
    self.stocks.fillna(0, inplace=True)  
    self.stocks.to_csv(self.group_file, index_label='stock')

    logger.info('group from {}/{}'.format(rev_year, rev_month))

  def check_buy(self, year, month, day):
    # 買點推薦 (跟訊號分開)
    year -= 1911
    date = "{}/{:02d}/{:02d}".format(year, month, day)
    stocks_wait = self.stocks[self.stocks['state']!=2].index
    for sn in stocks_wait:
      try: s = Stock(sn, date)
      except Exception as e:
        logger.error("{} |{}".format(e, sn))
        continue
      if self.stocks.loc[sn, 'state'] == 0:
        if s.large_volume() and s.low_price():
          # 低檔爆量長紅 -> 起漲 買 state = 2
          if s.long_red() and s.up(4):
            self.stocks.loc[sn, 'state'] = 2
            self.record.append(pd.DataFrame(index=[sn]))
            self.record.loc[sn, 'buy_price'] = s.close[-1]
            self.record.loc[sn, 'buy_date'] = date
            self.record.loc[sn, 'buy_comment'] = '低檔爆量長紅'
            self.stocks.loc[sn, 'target_price'] = s.close[-1]*1.2
            # print(self.stocks.loc[sn, 'year_avg'], self.stocks.loc[sn, 'month_avg'])

          # 低檔爆量且非長黑 -> 可布局 state = 1
          elif not s.long_black():
            self.stocks.loc[sn, 'state'] = 1
            logger.info("可布局 |{}".format(sn))
            # print(self.stocks.loc[sn, 'year_avg'], self.stocks.loc[sn, 'month_avg'])
    
      else:
        # state=1 連三日上5ma -> 買 state = 2
        if s.up_MA(3, 5) and s.low_price():
          self.stocks.loc[sn, 'state'] = 2
          self.record.append(pd.DataFrame(index=[sn]))
          self.record.loc[sn, 'buy_price'] = s.close[-1]
          self.record.loc[sn, 'buy_date'] = date
          self.record.loc[sn, 'buy_comment'] = '連三日上5均'
          self.stocks.loc[sn, 'target_price'] = s.close[-1]*1.2
          # print(self.stocks.loc[sn, 'year_avg'], self.stocks.loc[sn, 'month_avg'])


    self.stocks.to_csv(self.group_file, index_label='stock')
    self.record.to_csv(self.record_file, index_label='stock')

    logger.info("End ")
    

  def check_sell(self, year, month, day):
    year -= 1911
    date = "{}/{:02d}/{:02d}".format(year, month, day)
    stocks_buy = self.stocks[self.stocks['state']==2].index
    for sn in stocks_buy:
      try: s = Stock(sn, date)
      except Exception as e:
        logger.error("{} |{}".format(e, sn))
        continue
      # 停利
      if self.stocks.loc[sn, 'target_price'] < s.high[-1]:
        self.record.loc[sn, 'sell_price'] = self.stocks.loc[sn, 'target_price']
        self.record.loc[sn, 'sell_date'] = date
        self.record.loc[sn, 'sell_comment'] = '到目標價停利'
        self.stocks.loc[sn, 'state'] = 0
        self.stocks.loc[sn, 'target_price'] = 0
        print(self.record.loc[sn])
        self.result = self.result.append(self.record.loc[sn])
        self.record.drop(index=[sn], inplace=True)
      # 停損
      # elif s.close[-1] < s.MA(20):
      #   self.record.loc[sn, 'sell_price'] = s.close[-1]
      #   self.record.loc[sn, 'sell_date'] = date
      #   self.record.loc[sn, 'sell_comment'] = '跌破20日均停損'
      #   self.stocks.loc[sn, 'state'] = 0
      #   self.stocks.loc[sn, 'target_price'] = 0
      #   print(self.record.loc[sn])

    self.stocks.to_csv(self.group_file, index_label='stock')
    self.record.to_csv(self.record_file, index_label='stock')
    self.result.to_csv(self.result_file, index_label='stock')

  def update_target_price(self, year, month, day):
    year -= 1911
    # date = "{}/{:02d}/{:02d}".format(year, month, day)
    # stocks_buy = self.stocks[self.stocks['state']==2].index
    # for sn in stocks_buy:
    #   s = Stock(sn, date)
    #   if s.long_red():
    #     self.stocks.loc[sn, 'target_price'] = max(self.stocks.loc[sn, 'target_price'], s.close[-1]*1.03)

  def show_group_info(self, year, month):
    year = year-1911 if year > 1911 else year

    date = []
    for i in range(3):
      date.append("{}/{}".format(year, month))
      year = year if month!=1 else year-1
      month = month-1 if month!=1 else 12
    
    year_increase = by_stock(date, self.stocks.index, '營業收入-去年同月增減(%)', 'sii')
    month_increase = by_stock(date, self.stocks.index, '營業收入-上月比較增減(%)', 'sii')
    
    avg = pd.concat([year_increase.mean(), month_increase.mean()], axis=1).round(2)
    avg.columns = ['year_avg', 'month_avg']
    group_info = pd.concat([self.stocks, avg], axis=1)
    # tmp = group_info[(group_info['year_avg']<0)|(group_info['month_avg']<0)].sort_values('month_avg')
    tmp = group_info[(group_info['increase']==0)].sort_values('month_avg')
    # tmp = group_info[(group_info['increase']==0)].sort_values('year_avg')
    # tmp = group_info.loc[list(self.record.index)]
    # tmp = group_info.sort_values('year_avg')
    y = year_increase[tmp.index].T
    y.columns = [i+'_y' for i in y.columns]
    m = month_increase[tmp.index].T
    m.columns = [i+'_m' for i in m.columns]
    v = get_volume(tmp.index, '110/06')
    tmp = pd.concat([tmp, m, y, v], axis=1)
    # print(tmp.iloc[:10])
    # print(tmp[(tmp['volume'] < 300) & (tmp['state']==2)])
    print(tmp[tmp['year_avg'] < 10])

    # print(group_info.sort_values('month_avg'))  
    # .sort_values('high', ascending=False)


if __name__ == '__main__':
  g = Group()
  g.show_group_info(2021, 5)

