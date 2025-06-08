import geopandas as gpd
import pandas as pd 
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt

# ノードとエッジのデータを読み込み
nodes_gdf = gpd.read_file('./tmp/nodes.geojson')
edges_gdf = gpd.read_file('./tmp/edges.geojson')

# タンクのIDをtank.csvから読み込み
tank_csv = pd.read_csv('./tmp/tanks.csv')
tank_ids = tank_csv['ID'].tolist()  # タンクIDのリストを取得

# 空のグラフを作成
G = nx.Graph()

# ノードを追加
for idx, row in nodes_gdf.iterrows():
    G.add_node(row['key'], pos=(row.geometry.x, row.geometry.y))

# エッジを追加
for idx, row in edges_gdf.iterrows():
    G.add_edge(row['node_1'], row['node_2'])

# ノードのサイズ設定（全体はデフォルトサイズ50）
default_size = 50
highlight_size = 100

# サイズリストを作成
node_sizes = [highlight_size if node in tank_ids else default_size for node in G.nodes()]

# タンクの位置を取得
tank_positions = {tank_id: (nodes_gdf.loc[nodes_gdf['key'] == tank_id].geometry.values[0].x,
                            nodes_gdf.loc[nodes_gdf['key'] == tank_id].geometry.values[0].y)
                  for tank_id in tank_ids}

# ノードの座標を取得
node_positions = nx.get_node_attributes(G, 'pos')

# 各ノードと最も近いタンクとの距離を計算
node_distances = {}
for node, pos in node_positions.items():
    min_distance = np.min([np.linalg.norm(np.array(pos) - np.array(tank_pos))
                           for tank_pos in tank_positions.values()])
    node_distances[node] = min_distance

# 距離情報をノードに追加
nx.set_node_attributes(G, node_distances, 'distance_to_tank')

# ノードの色を距離に基づいて設定
node_colors = [G.nodes[node]['distance_to_tank'] for node in G.nodes()]

# プロットの設定
fig, ax = plt.subplots(figsize=(10, 8))

# 全体のノードを描画
nx.draw(G, pos=node_positions, node_color=node_colors, with_labels=False, node_size=node_sizes,
        cmap=plt.cm.Blues, edge_color='gray', ax=ax)

print(tank_positions)

# タンクノードを描画
if tank_positions:
    nx.draw_networkx_labels(G, pos=tank_positions, labels={node: node for node in tank_ids}, font_color='black')

plt.colorbar(plt.cm.ScalarMappable(cmap=plt.cm.Blues), fraction=0.1, pad=0.04, ax=ax, label='Distance to Nearest Tank')
plt.title('Heatmap of Node Distances to Nearest Tank')
plt.savefig(f"Heatmap of Node Distances to Nearest Tank.png", dpi=300)
plt.show()
