import geopandas as gpd
import matplotlib.pyplot as plt
import os 

os.makedirs("./tmp", exist_ok=True)

# gisデータの読み込み
shapefile_path = '../database/N01-07L-26-01.0_GML/N01_07L_26_Road.shp'
geojson_path = '../database/26100.geojson'

gdf1 = gpd.read_file(shapefile_path)
gdf2 = gpd.read_file(geojson_path)
gdf1.head()

# 重なる部分の取得
intersection_gdf = gpd.overlay(gdf1, gdf2, how='intersection')
intersection_gdf.to_file("./tmp/Kyoto-shi_road.geojson", driver="GeoJSON")
intersection_gdf.plot()
plt.title("Road of Kyoto-shi")
plt.show()

