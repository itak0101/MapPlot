# -*- coding: utf-8 -*-

#---------------------------------------------------------------------
# ライブラリの読み込み
#---------------------------------------------------------------------
import folium
import requests # Apache2 Licensed HTTP library
import json     # Data Format
from time import sleep
import csv
import pandas as pd
from geojson import Point, Polygon, Feature, FeatureCollection


#---------------------------------------------------------------------
# 標高ファイルを作成・出力する
#---------------------------------------------------------------------
def MakeHeightFile(fOriginLat,fOriginLon):

	# 出力ファイルのオープン
	fOutput = open("HeightList.csv", "w")
	fOutput.write("i,j,Lat,Lon,Height\n")
	
	# 標高データの取得と出力
	for i in range(-4,5):
		for j in range(-4,5):
			fLat = round(fOriginLat + (0.01 * i), 6)
			fLon = round(fOriginLon + (0.01 * j), 6)
			fHeight = GetHeight(fLat, fLon)
			fOutput.write("{0},{1},{2},{3},{4}\n".format(i, j, fLat, fLon, fHeight))
			
	# 出力ファイルのクローズ
	fOutput.close()


#---------------------------------------------------------------------
# 国土地理院Webから標高データを取得する
# API仕様: https://maps.gsi.go.jp/development/api.html
#---------------------------------------------------------------------
def GetHeight(fLat, fLon):

	# 国土地理院Webに付加を掛けすぎるとBANされるので少し間隔を置く
	sleep(2)

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

# 地図の中心座標を設定
fOriginLat = 35.7882773
fOriginLon = 138.997259

# 標高ファイルの作成
#MakeHeightFile(fOriginLat,fOriginLon)

# 地図データの作成 (+描画範囲の設定)
mapData = folium.Map(location=[fOriginLat,fOriginLon], zoom_start=13, tiles='Stamen Terrain')

# 標高ファイルの読み込み
hightList = pd.read_csv('HeightList.csv')

# ポリゴンをマップに追加
featureList = []
for i in range(-4,5):
	for j in range(-4,5):
		fLat = round(fOriginLat + (0.01 * i), 6)
		fLon = round(fOriginLon + (0.01 * j), 6)
		poly = Polygon([[(fLon-0.005, fLat-0.005), (fLon+0.005, fLat-0.005), (fLon+0.005, fLat+0.005), (fLon-0.005, fLat+0.005)]])
		feat = Feature(name='Test1', geometry=poly, id=999)
		featureList.append(feat)
my_feature_collection = FeatureCollection(featureList)
#print (my_feature_collection)
#print ('\n')
mapData.choropleth(
    name='choropleth',
    geo_data=my_feature_collection, # 形状データの設定 (GeoJSON形式で渡す)
    key_on='feature.id',            # 形状データの設定 (どの要素をキーとするか)
    data=hightList,                 # 標高値の設定 (Pandas行列データを渡す)
    columns=['i', 'Height'],        # 標高値の設定 (第一要素がキー、第二要素が値)
    fill_color='YlGn',              # 表示設定 (色)
    fill_opacity=0.4,               # 表示設定 (塗りつぶしの透明度)
    line_opacity=0.2,               # 表示設定 (線の透明度)
    legend_name='Height[m]'         # 表示設定 (凡例)
)

# 円マーカーをマップに追加
for i in range(0,len(hightList)):

    # 値取得
    fLat = float(hightList['Lat'][i])
    fLon = float(hightList['Lon'][i])
    fHeight = float(hightList['Height'][i])
    sColor = '#008000'
    popup = 'Safety'

    # 危険度判定
    if (isDanger(fHeight)):
        sColor = '#C9008A'
        popup = 'Danger'

    # デバッグ出力
    # print(str(fLat) + ',' + str(fLon) + ',' + str(fHeight) + ',' + sColor)

    # 地点情報を地図に追加してゆく
    folium.CircleMarker([fLat, fLon], radius=20, popup=popup, color=sColor, fill_color=sColor).add_to(mapData)

# 地図データをHTMLとして出力
mapData.save('map.html')


#---------------------------------------------------------------------
# メモ
#---------------------------------------------------------------------
#
# 地図の描画範囲を設定
#mapData = folium.Map(location=[-30.159215, 138.955078], zoom_start=4, tiles='Stamen Terrain')
#
## 都市のデータを配列で用意（本来はDBやcsvファイルから取得）
#cities = (
#    {'lat': -35.473468, 'lon': 149.012368, 'value': 1, 'name': 'Australian Capital Territory'},
#    {'lat': -31.253218, 'lon': 146.921099, 'value': 2, 'name': 'New South Wales'},
#    {'lat': -19.491411, 'lon': 132.550960, 'value': 3, 'name': 'Northern Territory'},
#    {'lat': -20.917574, 'lon': 142.702796, 'value': 4, 'name': 'Queensland'},
#    {'lat': -30.000232, 'lon': 136.209155, 'value': 5, 'name': 'South Australia'},
#    {'lat': -41.454520, 'lon': 145.970665, 'value': 6, 'name': 'Tasmania'},
#    {'lat': -37.471308, 'lon': 144.785153, 'value': 7, 'name': 'Victoria'},
#    {'lat': -27.672817, 'lon': 121.628310, 'value': 8, 'name': 'Western Australia'}
#)
#
## 都市のマーカーを追加
#for city in cities:
#    folium.CircleMarker(
#            [city['lat'], city['lon']],
#            radius=city['value'],
#            popup=city['name'],
#            color='#C9008A',
#            fill_color='#C9008A',
#    ).add_to(mapData)
#
## 地図データをHTMLとして出力
#mapData.save('map.html')
#
#
#
#
#latitude = '35.584047' 
#longitude = '139.665936'
#altitude = '14.000000'
#my_point = Point((float(longitude), float(latitude), float(altitude)))
#my_feature = Feature(geometry=my_point)
#my_feature_collection = FeatureCollection(my_feature)
#print my_feature_collection