import numpy as np
import pandas as pd
import collections
from log import setup_logger

logger = setup_logger('revenue_logger', './data/log/revenue.log')


def get_volume(stocks, month='110/01'):
  res = collections.defaultdict(list)
  for s in stocks:
    try:
      price = pd.read_csv('data/股價/{}.csv'.format(s), index_col=['日期'])
      v = price.loc[month+'/01':month+'/10', '成交股數'].mean() // 1000
      res[s].append(v)
    except Exception as e:
      logger.error("{} |{}".format(e, s))
      res[s].append(np.nan)
      
  return pd.DataFrame.from_dict(res, orient='index', columns=['volume'])


def by_stock(date, stocks, col, category):
  data = {s:[] for s in stocks}

  for d in date:
    y, m = d.split('/')
    df = pd.read_csv("data/月營收/{}_{}_{}.csv".format(y, m, category), index_col='公司代號')
    for s in stocks:
      try:
        data[s].append(df.loc[s][col])
      except:
        data[s].append(np.nan)
  df = pd.DataFrame.from_dict(data)
  df.index = date
  return df

def get_target(year, month, category):
  year = year-1911
  m = month+1 if not month == 12 else 1
  y = year if not month == 12 else year+1

  stocks = list(pd.read_csv("data/月營收/{}_{}_{}.csv".format(year, month, category))['公司代號'])
  date = []
  for i in range(3):
    date.append("{}/{}".format(year, month))
    year = year if month!=1 else year-1
    month = month-1 if month!=1 else 12
  # print(date)
  year_increase = by_stock(date, stocks, '營業收入-去年同月增減(%)', category)
  month_increase = by_stock(date, stocks, '營業收入-上月比較增減(%)', category)
  year_avg = year_increase[year_increase > 0].dropna(axis='columns').mean()
  month_avg = month_increase[month_increase > 0].dropna(axis='columns').mean()
  target = pd.concat([year_avg, month_avg], axis=1, join="inner").round(2)
  target.columns = ['year_avg', 'month_avg']
  # 取營收公布當月1~10號均量
  v = get_volume(target.index, '{}/{:02d}'.format(y, m))
  result = v[v['volume'] > 500]
  # tmp = pd.concat([target, v], axis=1)
  # target = target[tmp['volume'] > 500]
  
  return list(result.index)


  
  
if __name__ == '__main__':
  a = get_target(2020, 12, 'sii')
  print(a)
  # 沒爬上櫃股價
  # get_target(2020, 12, 'otc')
