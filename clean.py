import pandas as pd


r = pd.DataFrame(columns=['stock','buy_date','buy_price','sell_date','sell_price','buy_comment','sell_comment'])
g = pd.DataFrame(columns=['stock','state','increase', 'target_price'])

g.to_csv('./data/file/group.csv', index=False)
r.to_csv('./data/file/record.csv', index=False)
r.to_csv('./data/file/result.csv', index=False)

with open("test.txt", "w") as myfile:
  myfile.write('')