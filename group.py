import pandas as pd
import os
from revenue import get_target, by_stock, get_volume
from alert import Stock
from log import setup_logger
import datetime

logger = setup_logger('group_logger', './data/log/group.log')
to_bot = setup_logger('bot', './data/log/to_bot.log')

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
    year = year - 1911 if year>1911 else year
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
    rev = by_stock(date[:1], self.stocks.index, '營業收入-當月營收', 'sii')

    year_prod = (year_increase/100+1).prod()
    month_prod = (month_increase/100+1).prod()
    increase_prod = pd.concat([year_prod, month_prod, year_prod*month_prod, rev.T], axis=1).round(2)
    increase_prod.columns = ['year_prod', 'month_prod', 'prod', 'rev']
    group_info = pd.concat([self.stocks, increase_prod], axis=1)
    # tmp = group_info[(group_info['year_prob']<1)|(group_info['month_prob']<1)].sort_values('month_prob')
    tmp = group_info.sort_values('prod')
    # tmp = group_info[(group_info['increase']==1)].sort_values('prod')
    
    y = year_increase[tmp.index].T
    y.columns = [i+'_y' for i in y.columns]
    m = month_increase[tmp.index].T
    m.columns = [i+'_m' for i in m.columns]
    v = get_volume(tmp.index, '110/06')
    tmp = pd.concat([tmp, m, y, v], axis=1)
    print(tmp.describe().drop(columns=['state', 'increase', 'target_price']))
    print(tmp[tmp['prod']>10])
    """
    # tmp = group_info[(group_info['increase']==0)].sort_values('year_avg')
    tmp = group_info.loc[list(self.record.index)]
    print(tmp.iloc[:10])
    # print(tmp[(tmp['volume'] < 300) & (tmp['state']==2)])
    # print(tmp[tmp['year_avg'] < 10])

    # print(group_info.sort_values('month_avg'))  
    # .sort_values('high', ascending=False)
    """

  def revenue_highlight(self, year, month):
    year = year-1911 if year > 1911 else year
    filename = "data/月營收/{}_{}_{}.csv".format(year, month, 'sii')
    msg = []

    date = []
    for i in range(3):
      date.append("{}/{}".format(year, month))
      year = year if month!=1 else year-1
      month = month-1 if month!=1 else 12
    
    if not os.path.isfile(filename):
      return "無此資料"

    year_increase = by_stock(date, self.stocks.index, '營業收入-去年同月增減(%)', 'sii')
    month_increase = by_stock(date, self.stocks.index, '營業收入-上月比較增減(%)', 'sii')
    rev = by_stock(date[:1], self.stocks.index, '營業收入-當月營收', 'sii')

    year_prod = (year_increase/100+1).prod()
    month_prod = (month_increase/100+1).prod()
    increase_prod = pd.concat([year_prod, month_prod, year_prod*month_prod, rev.T], axis=1).round(2)
    increase_prod.columns = ['year_prod', 'month_prod', 'prod', 'rev']
    group_info = pd.concat([self.stocks, increase_prod], axis=1)
    # tmp = group_info[(group_info['year_prob']<1)|(group_info['month_prob']<1)].sort_values('month_prob')
    tmp = group_info.sort_values('prod', ascending=False)
    # tmp = tmp[tmp['prod']>10]
    
    y = year_increase[tmp.index].T
    y.columns = [i+'_y' for i in y.columns]
    m = month_increase[tmp.index].T
    m.columns = [i+'_m' for i in m.columns]
    t = datetime.date.today()
    v = get_volume(tmp.index, '{}/{:02d}'.format(t.year-1911, t.month))
    tmp = pd.concat([tmp, m, y, v], axis=1)
    # tmp_des = tmp.describe().drop(columns=['state', 'increase', 'target_price'])
    # print(tmp.describe().drop(columns=['state', 'increase', 'target_price']))
    # print(tmp)
    rank = pd.concat([tmp[x].rank(method='min', ascending=False) for x in ['prod', date[0]+'_y', date[0]+'_m', 'rev']], axis=1)
    rank.columns = ['增幅', '年增', '月增', '營收']
    name = by_stock(date[:1], rank.index, '公司名稱', 'sii')
    name.index = ['_']
    rank = pd.concat([name.T, rank, tmp[['prod',date[0]+'_y', date[0]+'_m' ,'rev', 'volume']]], axis=1)
    rank.to_csv('data/file/rev_all_sii.csv', index_label='stock')
    rank = rank[(rank[['增幅', '年增', '月增', '營收']]<=6).sum(axis=1)>0]

    filename = "data/file/rev_highlight_sii.csv"
    rank.to_csv(filename, index_label='stock')
    logger.info("save {}".format(filename))

    # fmt = ['{:10s}'.format, '{:4.2f}'.format]
    msg.append('{} 營收排名 ({})\n'.format(date[0], len(rank)))
    msg.append('增幅\n'+rank[['_', 'prod']].to_string(justify='center', header=False))
    msg.extend(['\n\n{}\n'.format(x) +
                rank.sort_values(x)[['_', y]][:6].to_string(justify='center', header=False) 
                for x, y in zip(['年增', '月增', '營收'], [date[0]+'_y', date[0]+'_m', 'rev'])])

    # print('\n'.join(msg))
    return '\n'.join(msg)

  def show_alert(self, year, month, day):
    year = year - 1911 if year>1911 else year
    date = "{}/{:02d}/{:02d}".format(year, month, day)

    def check_alert(stock):
      try: s = Stock(stock, date)
      except Exception as e:
        logger.error("{} |{}".format(e, stock))
        return None
      a = "{}".format(stock)

      if s.MA_long_sort() and s.MA_go_up(): 
        a += ",均線多頭排列且五日均上揚"
      else: a += ","

      if s.up_MA(3, 5): 
        a += ",連三日上五日均"
      else: a += ","

      if s.up_3_ma():
        a += ",收在三均之上"
      else: a += ","

      if s.MA_break_up():
        a += ",短均向上突破"
      else: a += ","

      if s.large_volume():
        a += ",爆量"
      else: a += ","

      if s.up(4):
        a += ",強勢"
      else: a += ","
      
      return a

    alert = list(self.stocks.index.map(lambda x: check_alert(x)))

    with open('data/file/alert_sii.csv', 'w') as f:
      f.write('\n'.join(alert))
    
    to_bot.info("End ")


  def read_alert_and_rev(self):
    alert = pd.read_csv('data/file/alert_sii.csv', header=None, index_col=0)
    rev = pd.read_csv('data/file/rev_all_sii.csv', index_col='stock')

    alert = alert.dropna(how='all')

    df = pd.concat([rev.loc[alert.index], alert], axis=1).sort_values('增幅')
    df.to_csv('data/file/rev_alert_sii.csv', index_label='stock')

    # return msg
    # 推薦: 均線多頭排列 & 五日均上揚 & 短均向上突破 & prod>2.5
    df = df[~(df[1].isna()|df[4].isna())]
    df = df[df['prod']>2.5]
    msg = ['推薦:'] 
    for r in df.iterrows():
      msg.append("{} {}".format(r[0], r[1]['_']))
    return '\n'.join(msg)

if __name__ == '__main__':
  
  g = Group()
  # g.show_group_info(2021, 5)
  # g.check_buy(2021, 7, 9)
  # g.revenue_highlight(2021, 6)
  
  g.show_alert(2021, 7, 27)
  msg = g.read_alert_and_rev()
  print(msg)
  # df = pd.read_csv("data/file/rev_alert_sii.csv", index_col='stock')
  # df = df[~(df['1'].isna()|df['4'].isna())]
  # msg = ['均線多頭排列 & 五日均上揚 & 短均向上突破：']
  # for r in df.iterrows():
  #   msg.append("{} {}".format(r[0], r[1]['_']))
  # print('\n'.join(msg))