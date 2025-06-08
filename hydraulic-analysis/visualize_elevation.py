import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd

# 標高データの取得
shapefile_path = '../database/G04a/5235/G04-56M_26-a-5235_ElevationAndSlopeAngleTertiaryMesh.shp'
data = gpd.read_file(shapefile_path)
# 元のデータのCRSを設定 (EPSG:4326が一般的なshpファイル)
data = data.set_crs(epsg=4326)
# 座標参照系をEPSG:3857に変換(webメルカトル)
data = data.to_crs(epsg=3857)

# ポリゴンの重心を取得
data['centroid'] = data.geometry.centroid

# 標高データの列名を指定
elevation_col = 'G04a_002'

# 数値に変換できない値をNaNに置き換え
data[elevation_col] = pd.to_numeric(data[elevation_col], errors='coerce')

# NaNを含む行を除外
valid_data = data.dropna(subset=[elevation_col])



# 緯度経度の範囲を指定
min_lon, max_lon = 1.5100e7, 1.5125e7
min_lat, max_lat = 4.150e6, 4.175e6

# 範囲内のデータを抽出
subset_data = valid_data.cx[min_lon:max_lon, min_lat:max_lat]

# 抽出したデータの重心座標と標高データを取得
subset_data['centroid'] = subset_data.geometry.centroid
subset_x = subset_data['centroid'].x
subset_y = subset_data['centroid'].y
subset_elevation = subset_data[elevation_col]

#ポリゴンの面積を計算しプロットの大きさを決める
subset_data['polygon_area'] = subset_data.geometry.area
# 幅（面積）を正規化してサイズマッピングする
min_area = subset_data['polygon_area'].min()
max_area = subset_data['polygon_area'].max()
subset_data['normalized_area'] = (subset_data['polygon_area'] - min_area) / (max_area - min_area)

print(subset_data['normalized_area'])
# 散布図の作成
plt.figure(figsize=(10, 8))
sc = plt.scatter(subset_x, subset_y, s=480, c=subset_elevation, cmap='jet', alpha=1, marker=",")
plt.colorbar(sc, label='Elevation (m)')
plt.title('Elevation map')
plt.xlabel('Longitude (EPSG:3857)')
plt.ylabel('Latitude (EPSG:3857)')
plt.grid(True)
plt.savefig(f"標高.png", dpi=300)
plt.show()

