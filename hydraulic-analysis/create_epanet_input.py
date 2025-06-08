# このスクリプトは、epanetの入力ファイルを作成する。
# create_graph_network.pyで作成したedges.geojsonとnodes.geojsonを読み込み、
# epanetの入力ファイルの形式に変換する。

# %% % --- % --- % --- % --- % --- % --- % --- % --- % --- % --- % ---
import pyogrio
import pandas as pd
import os

# %% % --- % --- % --- % --- % --- % --- % --- % --- % --- % --- % ---
edges = pyogrio.read_dataframe("./tmp/edges.geojson")
nodes = pyogrio.read_dataframe("./tmp/nodes.geojson")


df_keys = pd.read_csv('./tmp/matching_route_and_edges.csv')

# %% % --- % --- % --- % --- % --- % --- % --- % --- % --- % --- % ---
# TANKSは手動で追加
tank_lines = """;ID Elevation InitLevel MinLevel MaxLevel Diameter MinVol VolCurve Overflow
72 157 50 10 75 200 0 ;
137 210 50 10 75 200 0 ;
303 195 50 10 75 200 0 ;
"""

#グラフに値を載せたいのでタンク情報を書き出す####
tank_data = []
tank_ID=[]
for line in tank_lines.strip().split("\n")[1:]:
    parts = line.split()
    tank = {
        "ID": int(parts[0]),
        "Elevation": int(parts[1]),
        "InitLevel": int(parts[2]),
        "MinLevel": int(parts[3]),
        "MaxLevel": int(parts[4]),
        "Diameter": int(parts[5]),
        "MinVol": int(parts[6]),
    }
    tank_data.append(tank)
    
    ID=int(parts[0])#タンクIDの変更を後ろにも反映する用####
    tank_ID.append(ID)

df_tanks = pd.DataFrame(tank_data)

file_path='./tmp/tanks.csv'
df_tanks.to_csv(file_path, index=False, encoding='utf-8')

#
edges = edges.astype(
    {
        "key" : int, 
        "USE_AMOUNT": float,
        "PLANE_LENG": float,
        "DIAMETER": float,
        "ROUGHNESS": float,
        "node_1": int,
        "node_2": int,
    }
)

# REAL_LENGTが0だとエラーになるので、0.01を加算
edges["PLANE_LENG"] += 0.01

#出力先のディレクトリ内をクリーンする
def clear_directory(directory_path):
    """指定したディレクトリ内のファイルのみをすべて削除"""
    if os.path.exists(directory_path):
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print('Error file can not be deleted')

clear_directory('./tmp/input_files')#ディレクトリの中身を一度削除

#路線のCLOSE####
for k in range(0,len(df_keys)):
    route_key = df_keys.loc[k, 'Route Key']
    edges_keys = eval(df_keys.loc[k, 'Edges Keys'])
   
   # epanetの入力ファイルの形式に変換
    #edgesのstatusをクローズにする
    def get_line(row):
        if row['key'] in edges_keys:
            return f"{int(row['key'])} {int(row['node_1'])} {int(row['node_2'])} {float(row['PLANE_LENG'])} {int(row['DIAMETER'])} {int(row['ROUGHNESS'])} 0 CLOSED ;"
        else:
            return f"{int(row['key'])} {int(row['node_1'])} {int(row['node_2'])} {float(row['PLANE_LENG'])} {int(row['DIAMETER'])} {int(row['ROUGHNESS'])} 0 OPEN ;"
    edge_lines = "\n".join([get_line(row) for i, row in edges.iterrows()])

    nodes = nodes.astype(
        {
            "key": int,
            "elevation" : float,
        }
    )

    # edgesのuse_amountとelevationをnodesに分配
    nodes["use_amount"] = 0.0
    for i, row in edges.iterrows():
        nodes.loc[nodes["key"] == row["node_1"], "use_amount"] += row["USE_AMOUNT"] / 2
        nodes.loc[nodes["key"] == row["node_2"], "use_amount"] += row["USE_AMOUNT"] / 2

    # use_amountの単位をton/minからL/sに変換
    nodes["use_amount"] = nodes["use_amount"]

    # TANKSに含まれるノードを除外
    nodes = nodes[~nodes["key"].isin([tank_ID[0], tank_ID[1], tank_ID[2]])]

    # epanetの入力ファイルの形式に変換
    get_node = lambda row: f"{int(row['key'])} {int(row['elevation'])} {float(row['use_amount'])} ;"
    node_lines = "\n".join([get_node(row) for i, row in nodes.iterrows()])

    ###
    base_input_body = """
    [TITLE]
    Min Exec.

    [JUNCTIONS]

    [TANKS]

    [PIPES]

    [OPTIONS]
    Units LPS

    [END]
    """
    ###
    base_input_body = base_input_body.replace(
        "[PIPES]",
        "[PIPES]\n" + ";ID \t Node1 \t Node2 \t Length \t Diameter \t Roughness \t MinorLoss \t Status\n" + edge_lines,
    )
    base_input_body = base_input_body.replace(
        "[JUNCTIONS]",
        "[JUNCTIONS]\n" + ";ID \t Elev \t Demand \n" + node_lines,
    )
    base_input_body = base_input_body.replace(
        "[TANKS]",
        "[TANKS]\n" + tank_lines,
    )

    # save#inputの後ろの番号は損傷のため削除したエッジの名前####
    file_name = f"input{route_key}.inp"
    output_directory = './tmp/input_files'
    output_path = os.path.join(output_directory, file_name)

    # ディレクトリが存在しない場合は作成
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    with open(output_path, "w") as f:
        f.write(base_input_body)






