# -*- coding: utf-8 -*-

#---------------------------------------------------------------------
# ライブラリの読み込み
#---------------------------------------------------------------------
import folium
import requests # Apache2 Licensed HTTP library
import json     # Data Format
import csv
import pandas as pd
from time import sleep
from geojson import Point, Polygon, Feature, FeatureCollection


#---------------------------------------------------------------------
# 標高ファイルを作成・出力する
#---------------------------------------------------------------------
def MakeHeightFile(fOriginLat, fOriginLon, nGridCount, fGridSize):

	# 出力ファイルのオープン
	fOutput = open("HeightList.csv", "w")
	fOutput.write("id,i,j,Lat,Lon,Height\n")
	
	# 標高データの取得と出力
	for i in range(-nGridCount,nGridCount+1):
		for j in range(-nGridCount,nGridCount+1):
			fLat = round(fOriginLat + (fGridSize * i), 6)
			fLon = round(fOriginLon + (fGridSize * j), 6)
			fHeight = GetHeight(fLat, fLon)
			fOutput.write("{0}_{1},{2},{3},{4},{5},{6}\n".format(i, j, i, j, fLat, fLon, fHeight))

	# 出力ファイルのクローズ
	fOutput.close()


#---------------------------------------------------------------------
# 国土地理院Webから標高データを取得する
# API仕様: https://maps.gsi.go.jp/development/api.html
#---------------------------------------------------------------------
def GetHeight(fLat, fLon):

	# 国土地理院Webに負荷を掛けすぎないよう少し間隔を置く(秒単位で指定)
	sleep(3)

	# APIアクセスのURL設定
	sURL = 'http://cyberjapandata2.gsi.go.jp/general/dem/scripts/getelevation.php?lon={0}&lat={1}&outtype=JSON'.format(fLon, fLat)
	print(sURL)
	
	# APIにリクエストを送信する(実行結果・応答データがreqの中に格納される)
	req = requests.get(sURL)
	
	# APIからの受信データはJSON形式のためデコードする
	data = json.loads(req.text)
	
	# 受信データからキー項目を抽出する
	keyList = data.keys()
	sorted(keyList)
	
	# 送信データをそのまま出力
	#fOutput.write("#---- Request ----\n\n")
	#fOutput.write(sURL + "\n\n\n")
	#
	# 受信データをそのまま出力
	#fOutput.write("#---- Response (RawData) ----\n\n")
	#fOutput.write(req.text + "\n\n")
	#
	# 受信データのKey項目とそれに対応するValue項目を出力
	# (文字列処理による全件出力)
	#fOutput.write("\n#---- Responce (Keys & Values) ----\n")
	#nLine=0
	#for key in keyList:
	#	nLine+=1
	#	fOutput.write("\n")
	#	fOutput.write("   No: " + str(nLine) +"\n")
	#	fOutput.write("  Key: " + str(key) + "\n")
	#	sLine = str(data[key])
	#	sLine = sLine.replace("[","")
	#	sLine = sLine.replace("]","")
	#	valuelist = sLine.split(', ')
	#	for value in valuelist:
	#		value = value.replace("'","")
	#		fOutput.write("Value: " + value + "\n")

	# 標高データの抽出
	#print (type(data["elevation"]))   # 取得値の型の確認用
	fHeight = float(data["elevation"])
		
	# 取得結果(標高)を戻り値として返却する
	return fHeight


#---------------------------------------------------------------------
# 指定地点が危険か否かを判定する
#---------------------------------------------------------------------
def isDanger(fHeight):

	#標高1000m以上は危険と判定する
    if (1000.0 < fHeight):
        res = True
    else:
        res = False
    
    return res


#---------------------------------------------------------------------
# メイン処理
#---------------------------------------------------------------------

# ---- 設定 ----
# 地図の中心座標を設定
fOriginLat = 35.7882773   # 緯度
fOriginLon = 138.997259   # 経度

# 描画設定
nGridCount = 6            # 中心から上下左右に何グリッド描画する
fGridSize  = 0.002        # グリッドサイズ (緯度経度)


# ---- 標高ファイルの作成と読み込み ----
# 標高ファイルの作成 (国土地理院Webから標高データを取得)
MakeHeightFile(fOriginLat,fOriginLon,nGridCount,fGridSize)

# 標高ファイルの読み込み
heightList = pd.read_csv('HeightList.csv')

# 斜度判定 (標高データを基に傾斜の大きさを判定する)
gradient = []
for i in range(0,len(heightList)):
    # 当該地点の標高取得
    i2 = int(heightList['i'][i])
    j2 = int(heightList['j'][i])
    fHeight = float(heightList['Height'][i])
    
    # 周囲の最小標高取得
    fMinHeight = heightList[ ((i2-1)<=heightList['i']) & (heightList['i'] <= (i2+1)) & ((j2-1)<=heightList['j']) & (heightList['j'] <= (j2+1)) ]['Height'].min()
    fMinHeight = round(fMinHeight,1)

	# 周囲の最小標高と比較して、25%以上高ければ値を持たせる(1とする)
    if (0.25 < abs(fMinHeight-fHeight)/fMinHeight):
        gradient.append(1)
    else:
        gradient.append(0)
        
    # デバッグ用情報プロット
    #print('id=' + str(i2) + '_' + str(j2) + ' ' + 'Height=' + str(fHeight) + ' ' + 'AreaMinHeight=' + str(fMinHeight))

#斜度判定結果を配列に格納する(標高配列にGradient列として新規追加)
heightList['Gradient'] = gradient


## ---- 地図データを作成し、ポリゴンを重ねる ----
# 地図データの作成 (+初期表示設定)
mapData = folium.Map(location=[fOriginLat,fOriginLon], zoom_start=13, tiles='Stamen Terrain')

# ポリゴンデータを作成 (GeoJSON形式)
featureList = []
fHalfGrid  = (fGridSize/2.0)
for i in range(-nGridCount,nGridCount+1):
	for j in range(-nGridCount,nGridCount+1):
		id = str(i) + '_' + str(j)
		fLat = round(fOriginLat + (fGridSize * i), 6)
		fLon = round(fOriginLon + (fGridSize * j), 6)
		poly = Polygon([[(fLon-fHalfGrid, fLat-fHalfGrid), (fLon+fHalfGrid, fLat-fHalfGrid), (fLon+fHalfGrid, fLat+fHalfGrid), (fLon-fHalfGrid, fLat+fHalfGrid)]])
		feat = Feature(name=id, geometry=poly, id=id)
		featureList.append(feat)
my_feature_collection = FeatureCollection(featureList)

# GeoJSONデータの確認
#print (my_feature_collection)
#print ('\n')

# 形状データと標高データを紐付ける(斜度表示)
mapData.choropleth(
    name='choropleth',
    geo_data=my_feature_collection, # 形状データの設定 (GeoJSON形式で渡す)
    key_on='feature.id',            # 形状データの設定 (どの要素をキーとするか)
    data=heightList,                # 標高値の設定 (Pandas行列データを渡す)
    columns=['id', 'Gradient'],     # 標高値の設定 (第一要素がキー、第二要素が値)
    threshold_scale=[0,0.5,1],      # 凡例の設定
    fill_color='PuRd',              # 表示設定 (色)
    fill_opacity=0.4,               # 表示設定 (塗りつぶしの透明度)
    line_opacity=0.2,               # 表示設定 (線の透明度)
    legend_name='Gradient (Red:25% higher than neighbor minimum)'  # 表示設定 (凡例)
)
mapData.save('Output_Gradient.html')

# 形状データと標高データを紐付ける(標高表示)
mapData.choropleth(
    name='choropleth',
    geo_data=my_feature_collection, # 形状データの設定 (GeoJSON形式で渡す)
    key_on='feature.id',            # 形状データの設定 (どの要素をキーとするか)
    data=heightList,                # 標高値の設定 (Pandas行列データを渡す)
    columns=['id', 'Height'],       # 標高値の設定 (第一要素がキー、第二要素が値)
    threshold_scale=[0,600,800,1000,1200],    # 凡例の設定
    fill_color='PuRd',              # 表示設定 (色)
    fill_opacity=0.4,               # 表示設定 (塗りつぶしの透明度)
    line_opacity=0.2,               # 表示設定 (線の透明度)
    legend_name='Height[m]'         # 表示設定 (凡例)
)
mapData.save('Output_Height.html')

# 円マーカーをマップに追加
for i in range(0,len(heightList)):

    # 値取得
    fLat = float(heightList['Lat'][i])
    fLon = float(heightList['Lon'][i])
    fHeight = float(heightList['Height'][i])
    sColor = '#008000'
    popup = 'Safety'

    # 危険度判定 (TRUEの場合表示色を変更する)
    if (isDanger(fHeight)):
        sColor = '#C9008A'
        popup = 'Danger'

    # デバッグ出力
    # print(str(fLat) + ',' + str(fLon) + ',' + str(fHeight) + ',' + sColor)

    # 地点情報を地図に追加してゆく
    folium.CircleMarker([fLat, fLon], radius=20, popup=popup, color=sColor, fill_color=sColor).add_to(mapData)
mapData.save('Output_Height2.html')


#---------------------------------------------------------------------
# Reference
#---------------------------------------------------------------------
#
# [01] Folium QuickStart
# https://python-visualization.github.io/folium/quickstart.html
#
# [02] Folium 0.5.0 documentation
# http://python-visualization.github.io/folium/docs-v0.5.0/py-modindex.html
#
# [03] Python-GeoJson documentation
# https://python-geojson.readthedocs.io/en/latest/
#
# [04] 国土地理院 標高API 仕様
# https://maps.gsi.go.jp/development/api.html
#
# [05] #292 Choropleth map with Folium / python-graph-gallery.com
# https://python-graph-gallery.com/292-choropleth-map-with-folium/
#
#
#---------------------------------------------------------------------
# Memo
#---------------------------------------------------------------------
#
# [A] GeoJSON geopath line color
# 'BuGn', 'BuPu', 'GnBu', 'OrRd', 'PuBu', 'PuBuGn', 'PuRd', 'RdPu',
# 'YlGn', 'YlGnBu', 'YlOrBr', and 'YlOrRd'.