import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import json

# 1. 데이터 로딩
병원데이터 = pd.read_csv("data/병합_소아병원_좌표_통합.csv")
진료_병원_통계 = pd.read_csv("data/국민건강보험공단_시군구별 진료과목별 진료 정보_20231231.csv", encoding='EUC-KR')

# 진료과목명 컬럼명 확인 및 정리
진료_병원_통계 = 진료_병원_통계.rename(columns={"진료과목명": "진료과목", "시군구명": "시군구"})

# 진료과목 선택
selected_subject = st.selectbox("진료과목을 선택하세요", sorted(진료_병원_통계["진료과목"].dropna().unique()))

# 선택한 진료과목만 필터링
filtered_df = 진료_병원_통계[진료_병원_통계["진료과목"] == selected_subject]

# Choropleth용 데이터 생성
choropleth_data = filtered_df[["시군구", "진료인원(명)"]].copy()
choropleth_data.columns = ["지역명", "value"]
choropleth_data["value"] = pd.to_numeric(choropleth_data["value"], errors="coerce")
choropleth_data = choropleth_data.dropna().groupby("지역명", as_index=False).mean()

# 지역과 검색어 선택
region = st.selectbox("지역을 선택하세요", sorted(병원데이터["시군구코드명"].dropna().unique()))
search_keyword = st.text_input("병원명 또는 진료과목 검색", "")

# 병원 데이터 필터링
df = 병원데이터.copy()
df = df[df["시군구코드명"] == region]
if search_keyword:
    df = df[
        df["요양기관명"].str.contains(search_keyword, na=False, case=False) |
        df["진료과목내용명"].str.contains(search_keyword, na=False, case=False)
    ]

# 3. 지도 생성
m = folium.Map(location=[df["좌표(Y)"].mean(), df["좌표(X)"].mean()], zoom_start=12)
marker_cluster = MarkerCluster().add_to(m)

for _, row in df.iterrows():
    try:
        popup_info = f"{row['요양기관명']}<br>{row.get('진료과목내용명', '')}"
        folium.Marker(
            location=[row["좌표(Y)"], row["좌표(X)"]],
            popup=popup_info,
            icon=folium.Icon(color='blue', icon='plus-sign')
        ).add_to(marker_cluster)
    except:
        pass

# 4. Choropleth 지도 추가
with open("data/skorea_municipalities_geo_simple.json", encoding='utf-8') as f:
    geo_data = json.load(f)

folium.Choropleth(
    geo_data=geo_data,
    data=choropleth_data,
    columns=["지역명", "value"],
    key_on="feature.properties.name",
    fill_color="YlOrRd",
    fill_opacity=0.6,
    line_opacity=0.5,
    legend_name="지역별 병원 1곳당 진료인원",
    nan_fill_color="lightgray"
).add_to(m)

# 5. Streamlit에 지도 출력
st_data = st_folium(m, width=800, height=600)

# 6. 마커 클릭 시 병원 정보 표시
if st_data and st_data["last_object_clicked"]:
    clicked = st_data["last_object_clicked"]
    clicked_lat = clicked["lat"]
    clicked_lon = clicked["lng"]

    # 좌표 오차 허용
    tolerance = 0.0001
    matched = df[
        (abs(df["좌표(Y)"] - clicked_lat) < tolerance) &
        (abs(df["좌표(X)"] - clicked_lon) < tolerance)
    ]

    if not matched.empty:
        hospital = matched.iloc[0]
        st.subheader("🏥 선택한 병원 정보")
        st.markdown(f"**병원명:** {hospital['요양기관명']}")
        st.markdown(f"**진료과목:** {hospital.get('진료과목내용명', '정보 없음')}")
        st.markdown(f"**주소:** {hospital.get('주소', '정보 없음')}")
        st.markdown(f"**전화번호:** {hospital.get('전화번호', '정보 없음')}")
    else:
        st.warning("해당 위치의 병원 정보를 찾을 수 없습니다.")
