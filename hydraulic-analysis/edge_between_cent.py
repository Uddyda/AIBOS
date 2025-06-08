import geopandas as gpd
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# ノードとエッジのデータを読み込み
nodes_gdf = gpd.read_file('./tmp/nodes.geojson')
edges_gdf = gpd.read_file('./tmp/edges.geojson')

# 空のグラフを作成
G = nx.Graph()

# ノードを追加
for idx, row in nodes_gdf.iterrows():
    G.add_node(row['key'], geometry=row['geometry'])

# エッジを追加
for idx, row in edges_gdf.iterrows():
    G.add_edge(row['node_1'], row['node_2'])

# エッジの媒介中心性を計算
edge_betweenness = nx.edge_betweenness_centrality(G)

# 結果をエッジのGeoDataFrameに追加
edges_gdf['betweenness_centrality'] = edges_gdf.apply(
    lambda row: edge_betweenness[(row['node_1'], row['node_2'])], axis=1
)

# ヒートマップの作成
edges_gdf.plot(column='betweenness_centrality', cmap='OrRd', legend=True)
plt.title('Edge Betweenness Centrality')
plt.savefig(f"Edge Betweenness Centrality.png", dpi=300)
plt.show()
