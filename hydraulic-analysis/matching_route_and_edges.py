import json
import csv
import geopandas as gpd

# JSONファイルを読み込む関数
def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# 削除するノードのリストを読み込む
rosen = load_json_file('./tmp/rosen.json')

# データのJSONファイルを読み込む
edges_origin = load_json_file('./tmp/edges.geojson')
gdf_edges = gpd.read_file('./tmp/edges.geojson')


match_route_and_edgeskey=[]
#まず破損のない場合を追加
match_route_and_edgeskey.append({'Route Key': 0, 'Edges Keys': []})
# 次に、破損経路とそのパイプを結び付ける
for rosen_key, node_pairs in rosen.items():
    rosen_key=int(rosen_key)
    filtered_key = []
    for node_pair in node_pairs:
        node1_in_rosen = node_pair[0]
        node2_in_rosen = node_pair[1]
        # node1, node2 に対応するデータをフィルタリング
        for i in range(0,len(gdf_edges)):
            key_in_edges = gdf_edges['key'][i]
            node1_in_edges = gdf_edges['node_1'][i]
            node2_in_edges = gdf_edges['node_2'][i]

            if node1_in_edges==node1_in_rosen and node2_in_edges==node2_in_rosen:
                filtered_key.append(key_in_edges)
                gdf_edges.loc[gdf_edges['key'] == key_in_edges ,'route_key'] = rosen_key
            elif node1_in_edges==node2_in_rosen and node2_in_edges==node1_in_rosen:
                filtered_key.append(key_in_edges)
                gdf_edges.loc[gdf_edges['key'] == key_in_edges ,'route_key'] = rosen_key
            
    match_route_and_edgeskey.append({'Route Key': rosen_key, 'Edges Keys': filtered_key})


# NaN を '-1' で埋めて整数に変換
gdf_edges['route_key'] = gdf_edges['route_key'].fillna(-1).astype(int)
#edgesのデータをJSON ファイルに書き出す
gdf_edges.to_file("./tmp/edges.geojson", driver="GeoJSON")

# CSV ファイルに書き出す,-1はふくまないようにする
output_csv = './tmp/matching_route_and_edges.csv'

#※路線keyがgeojsonとcsv両方に出力されるが一長一短あってどちらも必要

with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Route Key', 'Edges Keys']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for data in match_route_and_edgeskey:
        writer.writerow(data)