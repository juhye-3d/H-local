import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import json
from streamlit_folium import st_folium

# 1. 데이터 로딩
병원데이터 = pd.read_csv("data/병합_소아병원_좌표_통합.csv")
진료_병원_통계 = pd.read_csv("data/국민건강보험공단_시군구별 진료과목별 진료 정보_20231231.csv", encoding='EUC-KR')

# 2. 진료 통계 데이터 전처리
진료_df = 진료_병원_통계.copy()
selected_subject = st.selectbox("진료과목을 선택하세요", sorted(진료_df["진료과목"].dropna().unique()))
filtered_df = 진료_df[진료_df["진료과목"] == selected_subject]

choropleth_data = filtered_df[["시군구", "진료인원(명)"]].copy()
choropleth_data.columns = ["지역명", "value"]
choropleth_data["value"] = pd.to_numeric(choropleth_data["value"], errors="coerce")
choropleth_data = choropleth_data.dropna()
choropleth_data = choropleth_data.groupby("지역명", as_index=False).mean()

# 3. 사용자 입력
region = st.selectbox("지역을 선택하세요", sorted(병원데이터["시군구코드명"].dropna().unique()))
search_keyword = st.text_input("병원명 또는 진료과목 검색", "")

lat = st.number_input("현재 위도 입력", value=37.5665)
lon = st.number_input("현재 경도 입력", value=126.9780)

# 4. 병원 데이터 필터링
df = 병원데이터.copy()
df = df[df["시군구코드명"] == region]

if search_keyword:
    df = df[
        df["요양기관명"].str.contains(search_keyword, na=False, case=False) |
        df["진료과목내용명"].str.contains(search_keyword, na=False, case=False)
    ]

# 5. 지도 생성
m = folium.Map(location=[lat, lon], zoom_start=12)
marker_cluster = MarkerCluster().add_to(m)

for _, row in df.iterrows():
    try:
        병원명 = row['요양기관명']
        진료과 = row.get('진료과목내용명', '')
        folium.Marker(
            location=[row['좌표(Y)'], row['좌표(X)']],
            popup=f"{병원명} ({진료과})",
            icon=folium.Icon(color='blue', icon='plus-sign')
        ).add_to(marker_cluster)
    except:
        pass

# 6. Choropleth 추가
with open("southkorea-maps/kostat/2013/json/skorea_municipalities_geo_simple.json", encoding='utf-8') as f:
    geo_data = json.load(f)

folium.Choropleth(
    geo_data=geo_data,
    data=choropleth_data,
    columns=['지역명', 'value'],
    key_on='feature.properties.name',
    fill_color='YlOrRd',
    fill_opacity=0.6,
    line_opacity=0.5,
    legend_name=f"지역별 '{selected_subject}' 진료인원",
    nan_fill_color='lightgray'
).add_to(m)

# 7. Streamlit에 지도 출력
st_data = st_folium(m, width=800, height=600)
