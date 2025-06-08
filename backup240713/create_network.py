import geopandas as gpd
import pyogrio
import matplotlib.pyplot as plt
import networkx as nx
from shapely.geometry import Point, LineString
import json

geojson_file_path = './tmp/Kyoto-shi_road.geojson'

GIS_FILE = geojson_file_path

# %% % --- % --- % --- % --- % --- % --- % --- % --- % --- % --- % ---
gdf_edges = pyogrio.read_dataframe(GIS_FILE)

# 削除する行のインデックスを格納するリスト
rows_to_remove = []

# 各行のジオメトリを処理
for i, line in enumerate(gdf_edges.geometry):
    if len(line.boundary.geoms) != 2:
        # 削除する行のインデックスを追加
        rows_to_remove.append(i)

# ジオメトリを削除する
gdf_edges = gdf_edges.drop(rows_to_remove)

# %% % --- % --- % --- % --- % --- % --- % --- % --- % --- % --- % ---
# 端点を取得
node_list = []
for line in gdf_edges.geometry:
    start, end = line.boundary.geoms
    node_list.extend([start, end])

# GeoDataFrameの作成
gdf = gpd.GeoDataFrame(geometry=node_list)
gdf_nodes = gpd.GeoDataFrame(geometry=node_list)

# 重複するノードの削除
gdf_nodes = gdf_nodes.drop_duplicates(subset="geometry").reset_index(drop=True)

# キーの割り当て
gdf_nodes["key"] = range(len(gdf_nodes))
# %% % --- % --- % --- % --- % --- % --- % --- % --- % --- % --- % ---
# エッジの各端点に対するノードのキーを検索するための辞書を作成
node_key_dict = gdf_nodes.set_index("geometry")["key"].to_dict()

# エッジの各端点に対するノードのキーを検索して追加
gdf_edges["node_1"] = gdf_edges.geometry.apply(
    lambda x: node_key_dict[x.boundary.geoms[0]]
)
gdf_edges["node_2"] = gdf_edges.geometry.apply(
    lambda x: node_key_dict[x.boundary.geoms[1]]
)

# # %% % --- % --- % --- % --- % --- % --- % --- % --- % --- % --- % --
# NetworkXグラフの作成
G = nx.Graph()

for _, node in gdf_nodes.iterrows():
    G.add_node(node['key'], geometry=node['geometry'])
for _, edge in gdf_edges.iterrows():
    G.add_edge(edge["node_1"], edge["node_2"], geometry=edge['geometry'])

components = list(nx.connected_components(G))
# 連結成分の数を数える

#小さい連結成分のノードを削除
for component in components:
    if len(component) <= 80:
        G.remove_nodes_from(component)

components = list(nx.connected_components(G))
num_components = len(components)
print("Number of connected components:", num_components)

# ネットワークを路線に分割して、保存
dfs_edges = list(nx.dfs_edges(G)) 
#print(dfs_edges)

rosens = {}
rosen = []
id = 1
flag = True
for s,g in dfs_edges:    
    if G.degree(s) == 2:
        rosen.append((s,g))
    else:
        if flag:
            rosen.append((s,g))
            flag = False
        else:
            pass
    if G.degree(g) == 2:
        pass
    else:
        rosens[f"{id}"] = rosen
        rosen = []
        id += 1
        flag = True
#print(rosens)

with open('./tmp/rosen.json', 'w') as f:
    json.dump(rosens, f, indent=2)


gdf_nodes = gpd.GeoDataFrame([(node, data['geometry']) for node, data in G.nodes(data=True)], columns=['key', 'geometry'])
gdf_edges = gpd.GeoDataFrame([(node_1, node_2, data['geometry']) for node_1, node_2, data in G.edges(data=True)], columns=['node_1', 'node_2', 'geometry'])

# ノードのGeoDataFrameをgeojsonとして保存
nodes_output_path = './tmp/nodes.geojson'
gdf_nodes.to_file(nodes_output_path, driver='GeoJSON')

# エッジのGeoDataFrameをgeojsonとして保存
edges_output_path = './tmp/edges.geojson'
gdf_edges.to_file(edges_output_path, driver='GeoJSON')

print(f"Nodes saved to {nodes_output_path}")
print(f"Edges saved to {edges_output_path}")

gdf = gpd.read_file('./tmp/edges.geojson')

gdf.plot()
plt.show()
