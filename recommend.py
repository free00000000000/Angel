from numpy.core.arrayprint import printoptions
import pandas as pd
import os
from revenue import get_target, by_stock, get_volume
import datetime
import numpy as np
import collections

def get_rev_month(month, day):
  if month > 2:
    if day >= 10: return month-1
    return month-2
  elif month == 2:
    if day >= 10: return 1
    else: return 12
  else:
    if day >= 10: return 12
    else: return 11

class Group:
  def __init__(self, year, month, day) -> None:
    self.year = year-1911 if year>1911 else year  # 轉民國
    self.month = month
    self.day = day
    self.rev_month = get_rev_month(self.month, self.day)
    self.rev_year = self.year if not self.rev_month == 12 else self.year-1
    self.group = self.set_group()

  def by_stock(self, date, stocks, category):
    data_year = {s:[] for s in stocks}
    data_month = {s:[] for s in stocks}

    for d in date:
      y, m = d.split('/')
      df = pd.read_csv("data/月營收/{}_{}_{}.csv".format(y, m, category), index_col='公司代號')
      for s in stocks:
        try: data_year[s].append(df.loc[s]['營業收入-去年同月增減(%)'])
        except: data_year[s].append(np.nan)
        try: data_month[s].append(df.loc[s]['營業收入-上月比較增減(%)'])
        except: data_month[s].append(np.nan)
    df_year = pd.DataFrame.from_dict(data_year)
    df_year.index = [d+'_year' for d in date]
    df_month = pd.DataFrame.from_dict(data_month)
    df_month.index = [d+'_month' for d in date]

    return pd.concat([df_year.T, df_month.T], axis=1)
  
  def get_volume(self, stocks, days=5):
    # days: 幾日均量
    date = '{}/{}/{}'.format(self.year, self.month, self.day)
    res = collections.defaultdict(list)
    for s in stocks:
      try:
        price = pd.read_csv('data/股價/{}.csv'.format(s), index_col=['日期'])
        v = price.loc[:date, '成交股數']
        v = v[-days:].mean() // 1000
        res[s].append(v)
      except Exception as e:
        print(s, e)
        res[s].append(np.nan)
        
    return pd.DataFrame.from_dict(res, orient='index', columns=['volume'])
  
  def set_group(self, m=3):
    # m: 幾個月的月營收
    stocks_sii = list(pd.read_csv("data/月營收/{}_{}_{}.csv".format(self.rev_year, self.rev_month, 'sii'))['公司代號'])
    stocks_otc = list(pd.read_csv("data/月營收/{}_{}_{}.csv".format(self.rev_year, self.rev_month, 'otc'))['公司代號'])
    date = []
    year, month = self.rev_year, self.rev_month
    for i in range(m):
      date.append("{}/{}".format(year, month))
      year = year if month!=1 else year-1
      month = month-1 if month!=1 else 12
      
    sii_rev = self.by_stock(date, stocks_sii, 'sii')
    otc_rev = self.by_stock(date, stocks_otc, 'otc')
    sii_org = sii_rev.copy()
    otc_org = otc_rev.copy()

    sii_rev = (sii_rev/100+1)
    otc_rev = (otc_rev/100+1)

    for i in range(3):
      sii_rev.iloc[:, i] = sii_rev.iloc[:, i].pow(3-i)
      sii_rev.iloc[:, i+3] = sii_rev.iloc[:, i+3].pow((3-i))

    sii_org['prod'] = sii_rev.prod(axis=1)
    sii_org = sii_org.sort_values('prod', ascending=False)
    sii_org = sii_org[sii_org['prod']>9]
    sii_org['volume'] = self.get_volume(sii_org.index)
    sii_org = sii_org[sii_org['volume']>2000]
    print(sii_org[:20])
    # print(sii_org.describe())

    otc_rev['prod'] = otc_rev.prod(axis=1)
    otc_rev = otc_rev[otc_rev['prod']>2].sort_values('prod', ascending=False)
    # from crawler import update_stock_price_otc
    # update_stock_price_otc(otc_rev.index, 110, 7)


    # otc_rev['volume'] = self.get_volume(otc_rev.index)
    # print(sii_rev[sii_rev['prod']>8])
    # print((sii_rev[:10]/100+1)*[3,2,1,3,2,1,0, 1])
    # print(sii_rev)

    # print(otc_rev[otc_rev['volume']>1000])
    
    # month_increase = by_stock(date, stocks, '營業收入-上月比較增減(%)', category)
    # year_avg = year_increase[year_increase > 0].dropna(axis='columns').mean()
    # month_avg = month_increase[month_increase > 0].dropna(axis='columns').mean()
    # target = pd.concat([year_avg, month_avg], axis=1, join="inner").round(2)
    # target.columns = ['year_avg', 'month_avg']
    # # 取營收公布當月1~10號均量
    # v = get_volume(target.index, '{}/{:02d}'.format(y, m))
    # result = v[v['volume'] > 500]
    # # tmp = pd.concat([target, v], axis=1)
    # # target = target[tmp['volume'] > 500]
    
    # return list(result.index)
    # target = get_target(rev_year, rev_month, 'sii')
    # print(target)
    # self.stocks = self.stocks.append(pd.DataFrame(index=target))
    # self.stocks = self.stocks[~self.stocks.index.duplicated(keep='first')]
    # self.stocks['increase'] = self.stocks.index.isin(target).astype(int)
    # self.stocks.fillna(0, inplace=True)  
    # self.stocks.to_csv(self.group_file, index_label='stock')


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

    # fmt = ['{:10s}'.format, '{:4.2f}'.format]
    msg.append('{} 營收排名 ({})\n'.format(date[0], len(rank)))
    msg.append('增幅\n'+rank[['_', 'prod']].to_string(justify='center', header=False))
    msg.extend(['\n\n{}\n'.format(x) +
                rank.sort_values(x)[['_', y]][:6].to_string(justify='center', header=False) 
                for x, y in zip(['年增', '月增', '營收'], [date[0]+'_y', date[0]+'_m', 'rev'])])

    # print('\n'.join(msg))
    return '\n'.join(msg)


if __name__ == '__main__':
  
  g = Group(2021, 7, 15)