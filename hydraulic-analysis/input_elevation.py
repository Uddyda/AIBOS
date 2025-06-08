import geopandas as gpd
import json
import matplotlib.pyplot as plt
from shapely.geometry import Point

shapefile_path = '../database/G04a/5235/G04-56M_26-a-5235_ElevationAndSlopeAngleTertiaryMesh.shp'
gdf = gpd.read_file(shapefile_path)
gdf_nodes = gpd.read_file('./tmp/nodes.geojson')

gdf_nodes['elevation'] = 100.0 # 'elevation' 列を初期化
# for i, node in gdf_nodes.iterrows():
#     node_point = Point(node['geometry'])
#     min_distance = float('inf')
#     for i2, geometry in enumerate(gdf['geometry']):
#         distance = node_point.distance(geometry)
#         if distance < min_distance:
#             min_distance = distance
#             nearest_index = i2
#         if geometry.contains(node_point):
#             gdf_nodes.at[i, 'elevation'] = gdf.at[i2, 'G04a_002']
#             break
#         else:
#             gdf_nodes.at[i, 'elevation'] = gdf.at[nearest_index, 'G04a_002']

# # 標高の値の平均を計算
# gdf_nodes['elevation'] = gdf_nodes['elevation'].astype(float)
# elevation_mean = gdf_nodes['elevation'].mean()

# # 標高が平均より100m高いノードのindexをリストに追加
# high_elevation_index = []
# for i, node in gdf_nodes.iterrows():
#     if node['elevation'] > (elevation_mean + 55):
#         high_elevation_index.append(i)

# print(f"標高の平均:{elevation_mean}")
# for idx in high_elevation_index:
#     print(f"標高の平均より50m高いノードのkey:{gdf_nodes.at[idx, 'key']}, 標高：{gdf_nodes.at[idx, 'elevation']}")

# エッジのGeoDataFrameをgeojsonとして保存
edges_output_path = './tmp/nodes.geojson'
gdf_nodes.to_file(edges_output_path, driver='GeoJSON')

#ノードの標高プロット####
# 元のデータのCRSを設定 (EPSG:4326が一般的なshpファイル)
gdf_nodes = gdf_nodes.set_crs(epsg=4326)
# 座標参照系をEPSG:3857に変換(webメルカトル)
gdf_nodes = gdf_nodes.to_crs(epsg=3857)

# 散布図の作成####
fig = plt.figure(figsize=(15, 5))

ax = fig.add_subplot(1, 2, 1)
gdf_nodes.plot(ax=ax, legend=False, column="elevation", cmap="jet", markersize=15)

# カラーバーの追加####
cb1 = plt.cm.ScalarMappable(cmap="jet", norm=plt.Normalize(vmin=gdf_nodes["elevation"].min(), vmax=gdf_nodes["elevation"].max()))
cb1._A = []  # この行はカラーバーを正しく表示するために必要
cbar = fig.colorbar(cb1, ax=ax)
cbar.set_label('Elevation (m)')

fig.savefig(f"ノード標高.png", dpi=300)