import json
import geopandas as gpd 
import pandas as pd
import glob
import os
import re
import pyogrio
import matplotlib.pyplot as plt

# ファイルパス
NORMAL_RESULT_PATH = "./tmp/results/results_input0.json" # 正常時の水理解析結果ファイルパス
ABNORMAL_RESULT_PATHS = glob.glob('./tmp/results/*.json')  
ABNORMAL_RESULT_PATHS = [s for s in ABNORMAL_RESULT_PATHS if "0" not in s] # 断水時の水理解析結果ファイルパス
INP_FILE = "./tmp/input_files/input0.inp" # 正常時のinputファイルパス

# パラメータの設定
A = 0.5 # 供給可能水量計算時の定数α
N = 4 # 各節点の需要者数
INCIDENT_PROB = 0.0001 # 断水路線の事故確率(件/年)

edges = pyogrio.read_dataframe("./tmp/edges.geojson")
edges["priority"] = -1.0
df_keys = pd.read_csv('./tmp/matching_route_and_edges.csv')
#print(df_keys.info())

for abnormal_file_path in ABNORMAL_RESULT_PATHS:
    # 水理解析結果の読み込み
    # 正常時結果ファイルを読み込んで、pandasdfに格納
    with open(NORMAL_RESULT_PATH,"r") as f:
        Nresult = json.load(f) # 辞書型で取得
    Ndf = pd.DataFrame(Nresult["nodes"])
    Ndf.rename(columns={'ノード番号': 'ID', '水圧':'正常水圧'}, inplace=True) # カラム名をIDと正常水圧に変更
    Ndf = Ndf.astype({'ID':int}) # IDを整数値に変更
    #print(Ndf.head())

    # 断水時結果ファイルを読み込んで、pandasdfに格納
    with open(abnormal_file_path,"r") as f:
        ABNresult = json.load(f) # 辞書型で取得
    ABNdf = pd.DataFrame(ABNresult["nodes"])
    ABNdf.rename(columns={'ノード番号': 'ID', '水圧':'異常水圧'}, inplace=True) # カラム名をIDと異常水圧に変更
    ABNdf = ABNdf.astype({'ID':int}) # IDを整数値に変更
    #print(ABNdf.head())

    # inputファイルからノードの需要水量を取り出して、pandasdfに格納
    nodes = [] # ノードの辞書型データを格納するリスト
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
    #print(demands.head())

    # ３つのdfをひとつにまとめる
    hdf = pd.merge(Ndf,ABNdf)
    hdf = pd.merge(hdf,demands)
    #print(hdf.head())

    # 正常時の最低水圧を減水率計算のしきい値として用いる
    BORDER = hdf['正常水圧'].min()
    #print(BORDER)

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

    #print(hdf.dtypes)
    #print(hdf.head())

    # 事故危険度Yaを算出
    Ya = Sav * INCIDENT_PROB

    # 被害影響度Ybを算出
    Yb = (hdf["節点減水率"]*hdf["需要者数"]).sum()

    # Ya*Ybを更新優先度指標とする
    priority = Ya * Yb

    file_name, file_extension = os.path.splitext(os.path.basename(abnormal_file_path))
    route_key = int(re.sub("results_input","",file_name)) 
    #print(hdf.info)
    #print(abnormal_file_path)
    #print(hdf.head())
    #print(route_key,Ya*Yb)
    edges_keys = eval(df_keys.loc[df_keys["Route Key"]==route_key, 'Edges Keys'].values[0])
    for edges_key in edges_keys:
        edges.loc[edges["key"]==edges_key,"priority"] = priority
    
edges['rank'] = edges['priority'].rank()
print(edges.head(20))

fig, ax = plt.subplots()
edges.plot(ax=ax, legend=False, column="rank", cmap="jet", markersize=15, vmin=edges["rank"].min(), vmax=edges["rank"].max())
cb1 = plt.cm.ScalarMappable(cmap="jet", norm=plt.Normalize(vmin=edges["rank"].min(), vmax=edges["rank"].max()))
cb1._A = []  # この行はカラーバーを正しく表示するために必要
cbar = fig.colorbar(cb1, ax=ax)
cbar.set_label('priority rank')

plt.savefig('./tmp/COF_result.png')
plt.show()

