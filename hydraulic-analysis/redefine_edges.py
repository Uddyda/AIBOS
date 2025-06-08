import geopandas as gpd 
import pandas as pd

gdf_edges = gpd.read_file('./tmp/edges.geojson')
df_rosen = pd.read_csv('./tmp/matching_route_and_edges.csv')

#gdf_edges = gdf_edges[["node_1","node_2","geometry"]]
print(gdf_edges)
#ノード座標を保持する辞書を作成する
gdf_edges.crs = "EPSG:4612"
gdf_edges_2451 = gdf_edges.to_crs(epsg=2451)  # UTM Zone 1Nの場合


#Linestringの長さを計算する
gdf_edges['PLANE_LENG'] = gdf_edges_2451['geometry'].length

#エッジのパラメータの追加
for key in range(len(gdf_edges)):
    if key in eval(df_rosen.loc[0, 'Edges Keys']):
        gdf_edges.loc[gdf_edges['key'] == key, 'USE_AMOUNT'] = 0.50
    else:
        gdf_edges.loc[gdf_edges['key'] == key, 'USE_AMOUNT'] = 0.10
    if key <= len(gdf_edges)/2:
        gdf_edges.loc[gdf_edges['key'] == key, 'DIAMETER'] =  100.0
        gdf_edges.loc[gdf_edges['key'] == key, 'ROUGHNESS'] = 140.0
    else:
        gdf_edges.loc[gdf_edges['key'] == key, 'DIAMETER'] =  200.0
        gdf_edges.loc[gdf_edges['key'] == key, 'ROUGHNESS'] = 100.0



gdf_edges.to_file("./tmp/edges.geojson", driver="GeoJSON")
