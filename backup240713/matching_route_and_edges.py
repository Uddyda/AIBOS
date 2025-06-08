import json
import csv

# JSONファイルを読み込む関数
def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# 削除するノードのリストを読み込む
rosen = load_json_file('./tmp/rosen.json')

# データのJSONファイルを読み込む
edges_origin = load_json_file('./tmp/edges.geojson')

match_route_and_edgeskey=[]
#まず破損のない場合を追加
match_route_and_edgeskey.append({'Route Key': 0, 'Edges Keys': []})
# 次に、破損経路とそのパイプを結び付ける
for key, node_pairs in rosen.items():
    filtered_key = []
    for node_pair in node_pairs:
        node1_in_rosen = node_pair[0]
        node2_in_rosen = node_pair[1]
        # node1, node2 に対応するデータをフィルタリング
        for feature in edges_origin['features']:
            key_in_edges = feature['properties']['key']
            node1_in_edges = feature['properties']['node_1']
            node2_in_edges = feature['properties']['node_2']

            if node1_in_edges==node1_in_rosen and node2_in_edges==node2_in_rosen:
                filtered_key.append(key_in_edges)
            elif node1_in_edges==node2_in_rosen and node2_in_edges==node1_in_rosen:
                filtered_key.append(key_in_edges)
    
    match_route_and_edgeskey.append({'Route Key': key, 'Edges Keys': filtered_key})

'''
# JSON ファイルに書き出す
output_json = './tmp/matching_route_and_edges.json'

with open(output_json, 'w', encoding='utf-8') as jsonfile:
    json.dump(match_route_and_edgeskey, jsonfile, indent=4, ensure_ascii=False)


'''
# CSV ファイルに書き出す
output_csv = './tmp/matching_route_and_edges.csv'

with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Route Key', 'Edges Keys']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for data in match_route_and_edgeskey:
        writer.writerow(data)