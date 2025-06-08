import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import json
from streamlit_folium import st_folium

# 데이터 로드
병원데이터 = pd.read_csv("전국_소아과_병원목록.csv")  # GitHub에 업로드 필요

# 사용자 입력
region = st.selectbox("지역 선택", sorted(병원데이터["시군구코드명"].dropna().unique()))
keyword = st.text_input("검색어 입력", "")

lat = st.number_input("위도", value=37.5665)
lon = st.number_input("경도", value=126.9780)

# 필터링
df = 병원데이터[병원데이터["시군구코드명"] == region]
if keyword:
    df = df[
        df["요양기관명"].str.contains(keyword, na=False, case=False) |
        df["진료과목내용명"].str.contains(keyword, na=False, case=False)
    ]

# 지도 생성
m = folium.Map(location=[lat, lon], zoom_start=12)
marker_cluster = MarkerCluster().add_to(m)
for _, row in df.iterrows():
    try:
        folium.Marker(
            location=[row['좌표(Y)'], row['좌표(X)']],
            popup=row['요양기관명'],
            icon=folium.Icon(color='blue')
        ).add_to(marker_cluster)
    except:
        pass

# 지도 출력
st_folium(m, width=800, height=600)
