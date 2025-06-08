import json
import geopandas as gpd 
import pandas as pd
import glob
import os
import numpy as np
import re
import pyogrio
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

# ファイルパス
NORMAL_RESULT_PATH = "./tmp/results/results_input0.json" # 正常時の水理解析結果ファイルパス
ABNORMAL_RESULT_PATHS = glob.glob('./tmp/results/*.json')  
ABNORMAL_RESULT_PATHS = [s for s in ABNORMAL_RESULT_PATHS if "input0" not in s] # 断水時の水理解析結果ファイルパス
INP_FILE = "./tmp/input_files/input0.inp" # 正常時のinputファイルパス

# パラメータの設定
A = 0.5 # 供給可能水量計算時の定数α
N = 4 # 各節点の需要者数
INCIDENT_PROB = 0.0001 # 断水路線の事故確率(件/年)

edges = pyogrio.read_dataframe("./tmp/edges.geojson")
edges["Priority_value"] = -1.0
df_keys = pd.read_csv('./tmp/matching_route_and_edges.csv')
#print(df_keys.info())

route_rank_list=[]
for abnormal_file_path in ABNORMAL_RESULT_PATHS:
    # 水理解析結果の読み込み
    # 正常時結果ファイルを読み込んで、pandasdfに格納
    with open(NORMAL_RESULT_PATH,"r") as f:
        Nresult = json.load(f) # 辞書型で取得
    Ndf = pd.DataFrame(Nresult["nodes"])
    Ndf.rename(columns={'ノード番号': 'ID', '水圧':'正常水圧'}, inplace=True) # カラム名をIDと正常水圧に変更
    Ndf = Ndf.astype({'ID':int}) # IDを整数値に変更

    # 断水時結果ファイルを読み込んで、pandasdfに格納
    with open(abnormal_file_path,"r") as f:
        ABNresult = json.load(f) 
    ABNdf = pd.DataFrame(ABNresult["nodes"])
    ABNdf.rename(columns={'ノード番号': 'ID', '水圧':'異常水圧'}, inplace=True) # カラム名をIDと異常水圧に変更
    ABNdf = ABNdf.astype({'ID':int}) # IDを整数値に変更

    # inputファイルからノードの需要水量を取り出して、pandasdfに格納
    nodes = [] 
    # inputファイルの読み込み
    with open(INP_FILE, 'r') as f:
        lines = f.readlines() # 行をリストに格納 
    link_section = False 
    # nodeのデータを取り出す
    for line in lines:
        line = line.strip()   # 入力を揃えるため両端の空白文字と;
        line = line.replace(';', '') # を削除
        # [JUNCTIONS]で始まればフラグをTrueにする
        if line.startswith("[JUNCTIONS]"):
            link_section = True
        # 空白行でフラグをFalseにする
        elif not line:
            link_section = False
        # 要素名の行は無視する
        elif line.startswith("ID"):
            pass
        # データの行は要素を分割して、ノードの情報をグラフにいれる
        elif link_section and line.strip():
            parts = line.split()
            nodes.append({"ID":int(parts[0]), "水需要量":float(parts[2])})
    demands = pd.DataFrame(nodes)

    # ３つのdfをひとつにまとめる
    hdf = pd.merge(Ndf,ABNdf)
    hdf = pd.merge(hdf,demands)

    # 正常時の最低水圧を減水率計算のしきい値として用いる
    BORDER = hdf['正常水圧'].min()

    def calc_useable_water(hdf):
        if hdf['異常水圧'] <= 0:
            result = 0
        elif hdf['異常水圧'] >= BORDER:
            result = hdf['水需要量']
        elif 0 < hdf['異常水圧'] < BORDER:
            result = ((hdf['異常水圧']/BORDER)**A)*hdf['水需要量']
        return result

    def calc_decrease_rate(hdf):
        if hdf['水需要量'] == 0:
            result = 0
        else:
            result = (hdf['水需要量']-hdf["供給可能水量"])/hdf['水需要量']
        return result

    hdf["供給可能水量"] = hdf.apply(calc_useable_water,axis=1)
    hdf["節点減水率"] = hdf.apply(calc_decrease_rate,axis=1)

    # 全体減水率の計算
    Sav = (hdf['水需要量'].sum()-hdf['供給可能水量'].sum())/hdf['水需要量'].sum()
    #print(whole_decrease_rate)

    # 節点需要者数の設定
    hdf["需要者数"] = N

    # 事故危険度Yaを算出
    Ya = Sav * INCIDENT_PROB

    # 被害影響度Ybを算出
    Yb = (hdf["節点減水率"]*hdf["需要者数"]).sum()

    # Ya*Ybを更新優先度指標とする
    priority = Ya * Yb

    file_name, file_extension = os.path.splitext(os.path.basename(abnormal_file_path))
    route_key = int(re.sub("results_input","",file_name)) 
    route_rank_list.append({'Route_key': route_key, 'Priority_value': priority})
    edges_keys = eval(df_keys.loc[df_keys["Route Key"]==route_key, 'Edges Keys'].values[0])
    for edges_key in edges_keys:
        edges.loc[edges["key"]==edges_key,"Priority_value"] = priority

df_route = pd.DataFrame(route_rank_list)
#まず、路線番号に更新優先度ランクをつけ、そのあとに各エッジにランクを当てはめる
df_route['rank'] = df_route['Priority_value'].rank()
df_route = df_route.sort_values(by='Route_key')
print(df_route)
print(len(df_route))
print(edges)

Route_list=df_route['Route_key'].tolist()
for index,row in edges.iterrows():
    route_key = row['route_key']
    rank = df_route.loc[df_route['Route_key'] == route_key, 'rank']
    if not rank.empty:
        edges.at[index, 'Priority_Rank'] = rank.iloc[0]
    else:
        edges.at[index, 'Priority_Rank'] = 0

'''
#路線ではなくエッジでランク付けしてたやつ
for i in range(0,len(df_route)-1):
    print(i)
    route = df_route.loc[i,'Route_key']
    rank = df_route.loc[i,'rank']
    for key in edges['route_key']:
        key=int(key)
        if key >=0:
            edges.loc[edges['route_key'] == route, 'Priority_Rank'] = rank
        else:
            edges.loc[edges['route_key'] == route, 'Priority_Rank'] = 0
'''
edges.to_file("./tmp/update_edges.geojson", driver="GeoJSON")

# プロットの作成
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

# Priority Map
edges.plot(ax=ax1, legend=False, column="Priority_value", cmap="jet", markersize=15, vmin=edges["Priority_value"].min(), vmax=edges["Priority_value"].max())
cb1 = plt.cm.ScalarMappable(cmap="jet", norm=plt.Normalize(vmin=edges["Priority_value"].min(), vmax=edges["Priority_value"].max()))
cb1._A = []  # この行はカラーバーを正しく表示するために必要
cbar1 = fig.colorbar(cb1, ax=ax1)
cbar1.set_label('Priority Value')
ax1.set_title('Priority Map')

# Rank Map
edges.plot(ax=ax2, legend=False, column="Priority_Rank", cmap="jet", markersize=15, vmin=edges["Priority_Rank"].min(), vmax=edges["Priority_Rank"].max())
cb2 = plt.cm.ScalarMappable(cmap="jet", norm=plt.Normalize(vmin=edges["Priority_Rank"].min(), vmax=edges["Priority_Rank"].max()))
cb2._A = []  # この行はカラーバーを正しく表示するために必要
cbar2 = fig.colorbar(cb2, ax=ax2)
cbar2.set_label('Priority Rank')
ax2.set_title('Rank Map')

#

plt.savefig('./tmp/COF_result.png')
plt.show()
