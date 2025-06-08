# このスクリプトは、EPANETの結果を可視化する。
# convert_output_to_json.pyで作成したjsonファイルを読み込み、
# 水圧や流量の可視化を行う。

# %% % --- % --- % --- % --- % --- % --- % --- % --- % --- % --- % ---
import json
import pandas as pd
import pyogrio
import matplotlib.pyplot as plt
import os

# %% % --- % --- % --- % --- % --- % --- % --- % --- % --- % --- % ---
df_keys = pd.read_csv('./tmp/matching_route_and_edges.csv')
for k in range(0,len(df_keys)):
    dyna_file=f'results_input{k}.json'
    filepath = f"./tmp/results/{dyna_file}"

    with open(filepath, "r") as f:
        result = json.load(f)

    nodes = pyogrio.read_dataframe("./tmp/nodes.geojson")

    # # nodes['key']をstrに変換

    edges = pyogrio.read_dataframe("./tmp/edges.geojson")

    node_id_set = []
    tank_id_set = []
    node_pressure_set = []
    tank_pressure_set = []

    # inputファイルからタンクのIDを取り出す
    TANK_ID = [] # タンクのIDを保存するリスト
    INP_FILE = "./tmp/input.inp" #インプットファイルのパス

    # inputファイルの読み込み
    with open(INP_FILE, 'r') as f:
        lines = f.readlines() # 行をリストに格納 
    link_section = False 
    # TANKのIDを取り出す
    for line in lines:
        line = line.strip() # 入力を揃えるため両端の空白文字を削除
        # [TANKS]で始まればフラグをTrueにする
        if line.startswith("[TANKS]"):
            link_section = True
        # 空白行でフラグをFalseにする
        elif not line:
            link_section = False
        # 要素名の行は無視する
        elif line.startswith(";ID"):
            pass
        # データの行は要素を分割して、ノードの情報をグラフにいれる
        elif link_section and line.strip():
            parts = line.split()
            TANK_ID.append(int(parts[0]))
    # print(TANK_ID)

    # タンクとタンク以外のノードのID、水圧をそれぞれリストに格納する
    for node in result["nodes"]:
        if node["ノード番号"] in TANK_ID:
            tank_id_set.append(node["ノード番号"])
            tank_pressure_set.append(node["水圧"])
        else:
            node_id_set.append(node["ノード番号"])
            node_pressure_set.append(node["水圧"])

    # key: node_idset, head: head_setのdfを作成
    nodes_df = pd.DataFrame({"key": node_id_set, "pressure": node_pressure_set})
    tanks_df = pd.DataFrame({"key": tank_id_set, "pressure": tank_pressure_set})

    # dfとnodesを結合
    nodes_merged = pd.merge(nodes, nodes_df, on="key")
    tanks_merged = pd.merge(nodes, tanks_df, on="key")

    # データの座標参照系をEPSG:3857に変換（Webメルカトル投影）
    nodes_merged.crs = "EPSG:4612"
    nodes_3857 = nodes_merged.to_crs("EPSG:3857")
    tanks_merged.crs = "EPSG:4612"
    tanks_3857 = tanks_merged.to_crs("EPSG:3857")

    edges.crs = "EPSG:4612"
    edges_3857 = edges.to_crs("EPSG:3857")

    # プロットの設定
    fig = plt.figure(figsize=(15, 5))

    ax = fig.add_subplot(1, 2, 1)
    nodes_3857.plot(ax=ax, legend=False, column="pressure", cmap="jet", markersize=15)
    tanks_3857.plot(ax=ax, legend=False, marker='s', cmap="jet", markersize=150)
    edges_3857.plot(ax=ax, color="black", linewidth=0.5)

    # 各タンクの点の近くにタンクIDを表示する####
    for index, row in tanks_3857.iterrows():
        x, y = row['geometry'].x, row['geometry'].y
        tank_id = row['key']
        ax.annotate(tank_id, (x, y), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=10)

    # カラーバーの追加####
    cb1 = plt.cm.ScalarMappable(cmap="jet", norm=plt.Normalize(vmin=nodes_3857["pressure"].min(), vmax=nodes_3857["pressure"].max()))
    cb1._A = []  # この行はカラーバーを正しく表示するために必要
    cbar = fig.colorbar(cb1, ax=ax)
    cbar.set_label('Pressure (Pa)')
    # # %% % --- % --- % --- % --- % --- % --- % --- % --- % --- % --- % ---
    edge_id_set = []
    flow_set = []

    for edge in result["links"]:
        edge_id_set.append(edge["リンク番号"])
        flow_set.append(edge["流量"])

    df = pd.DataFrame({"key": edge_id_set, "flow": flow_set})

    # flowはabsをとる
    df["flow"] = df["flow"].abs()

    # dfとedgeを結合
    edges_merged = pd.merge(edges, df, on="key")
    edges_merged.crs = "EPSG:4612"
    edges_3857 = edges_merged.to_crs("EPSG:3857")

    # プロットの設定
    ax = fig.add_subplot(1, 2, 2)
    edges_3857.plot(ax=ax, legend=False, column="flow", cmap="jet", markersize=15)

    # タンクのプロットとID表示####
    for index, row in tanks_3857.iterrows():
        x, y = row['geometry'].x, row['geometry'].y
        ax.scatter(x, y, color='black', s=150, marker='s')
        tank_id = row['key']
        ax.annotate(tank_id, (x, y), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=10)

    #単位付きカラーバーの追加####
    cb2 = plt.cm.ScalarMappable(cmap="jet", norm=plt.Normalize(vmin=edges_3857["flow"].min(), vmax=edges_3857["flow"].max()))
    cb2._A = []  # この行はカラーバーを正しく表示するために必要
    cbar = fig.colorbar(cb2, ax=ax)
    cbar.set_label('Flow (m³/s)')

    #タンク情報の表示とinputファイル名の表示####
    df_tanks = pd.read_csv('./tmp/tanks.csv')
    text_x = 0.58 
    text_y_initial = 0.4 
    text_y_step = 0.117  # 各行ごとにy座標をどれだけずらすか

    for index, row in df_tanks.iterrows():
        tank_id = row['ID']
        tank_elevation = row['Elevation']
        tank_pressure = row['InitLevel']
        text_y = text_y_initial - index * text_y_step
        text = f"Tank ID: {tank_id},\n Elevation: {tank_elevation},\n Initial Pressure: {tank_pressure}"
        fig.text(text_x, text_y, text, fontsize=10, ha='right', va='bottom', bbox=dict(facecolor='white', alpha=0.5))
    
    #インプットファイルの名前を出力
    text = f"input{k}"
    fig.text(0.56, 0.8, text, fontsize=15, ha='right', va='bottom', bbox=dict(facecolor='white', alpha=0.5))

    # プロットの表示
    plt.show()
    fig.savefig(f"./tmp/image_results/{os.path.basename(dyna_file)}.png", dpi=300)

