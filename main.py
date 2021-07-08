from datetime import date
from crawler import get_revenue, update_stock_price
from group import Group

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

def update():
  now = date.today()
  rev_month = get_rev_month(now.month, now.day)
  g = Group()

  if now.isoweekday() <= 5:  # 星期一~五
    rev_year = now.year if not rev_month == 12 else now.year-1

    if get_revenue(rev_year, rev_month):  # 有新的營收
      g.update(rev_year, rev_month)  # 更新觀察股
    
    # 更新觀察股的股價
    update_stock_price(list(g.stocks.index))

    # show_alert(now.year, now.month, now.day)  # 買賣訊號提醒
    g.check_buy(now.year, now.month, now.day)
    g.check_sell(now.year, now.month, now.day)
    # g.update_target_price(now.year, now.month, now.day)


if __name__ == '__main__':
  # g = Group()
  pass