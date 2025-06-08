import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import json
from streamlit_folium import st_folium

# 1. 데이터 로딩
병원데이터 = pd.read_csv("data/병합_소아병원_좌표_통합.csv")
진료_병원_통계 = pd.read_csv("data/국민건강보험공단_시군구별 진료과목별 진료 정보_20231231.csv", encoding='EUC-KR')

# 2. 상단 제목 표시
st.title("소아청소년과 병원 지도")

# 👉 진료과목 필터링을 코드상으로 고정
filtered_df = 진료_병원_통계[진료_병원_통계["진료과목명"] == "소아청소년과"]

# 👉 Choropleth용 데이터 생성
choropleth_data = filtered_df[["시군구명", "진료인원(명)"]].copy()
choropleth_data.columns = ["지역명", "value"]
choropleth_data["value"] = pd.to_numeric(choropleth_data["value"], errors="coerce")
choropleth_data = choropleth_data.dropna()
choropleth_data = choropleth_data.groupby("지역명", as_index=False).mean()

# 3. 지역 선택 및 검색
region = st.selectbox("지역을 선택하세요", sorted(병원데이터["시군구코드명"].dropna().unique()))
search_keyword = st.text_input("병원명 검색", "")

# 4. 병원 데이터 필터링
df = 병원데이터.copy()
df = df[df["시군구코드명"] == region]

if search_keyword:
    df = df[df["요양기관명"].str.contains(search_keyword, na=False, case=False)]

# 5. 지도 생성
m = folium.Map(location=[36.5, 127.8], zoom_start=7)
marker_cluster = MarkerCluster().add_to(m)

for _, row in df.iterrows():
    try:
        병원명 = row['요양기관명']
        주소 = row.get('주소', '')
        folium.Marker(
            location=[row['좌표(Y)'], row['좌표(X)']],
            popup=f"{병원명}<br>{주소}",
            icon=folium.Icon(color='blue', icon='plus-sign')
        ).add_to(marker_cluster)
    except:
        pass

# 6. Choropleth
with open("data/skorea_municipalities_geo_simple.json", encoding='utf-8') as f:
    geo_data = json.load(f)

folium.Choropleth(
    geo_data=geo_data,
    data=choropleth_data,
    columns=['지역명', 'value'],
    key_on='feature.properties.name',
    fill_color='YlOrRd',
    fill_opacity=0.6,
    line_opacity=0.5,
    legend_name='지역별 병원당 진료인원',
    nan_fill_color='lightgray'
).add_to(m)

# 7. 지도 출력
st_data = st_folium(m, width=800, height=600)
