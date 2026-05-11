import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

def fetch_bunjang(keyword):
    all_products =[]
    page = 0
    three_months_ago = datetime.now() - timedelta(days=90)
    keywords = keyword.lower().split()
    
    # 목표: 최소 50개 이상 OR 3개월치 전체
    while len(all_products) < 50 or (all_products and all_products[-1]['날짜'] >= three_months_ago):
        url = f"https://api.bunjang.co.kr/api/1/find_v2.json?q={keyword}&order=date&page_size=50&page={page}"
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            data = response.json()
            items = data.get('list',[])
            
            if not items or page > 20: break # 최대 20페이지까지만 탐색
            
            for item in items:
                name = item.get('name', '').lower()
                if not all(k in name for k in keywords) or '본체' in name: continue
                if '삽니다' in name or '구매' in name or '구함' in name: continue
                ts = item.get('update_time', 0)
                date_obj = datetime.fromtimestamp(ts) if ts > 0 else datetime.now()
                
                all_products.append({
                    "날짜": date_obj,
                    "제목": item.get('name'),
                    "가격": int(item.get('price', 0)),
                    "작성자": item.get('user_name', '알수없음'),
                    "pid": item.get('pid')
                })
            page += 1
        except:
            break
            
    return pd.DataFrame(all_products)

st.set_page_config(layout="wide")
st.title("💰 디지털 시세 분석기 (3개월/최소50개 기준)")

keyword = st.text_input("검색할 키워드 입력:")
# ... (앞부분 생략) ...

if keyword:
    with st.spinner('데이터 수집 및 분석 중...'):
        df = fetch_bunjang(keyword)
    
    if not df.empty:
        # 데이터 정제 및 필터링
        df = df[df['가격'] > 10000]
        if len(df) > 10:
            df = df.sort_values(by="가격")
            df = df.iloc[5:-5]
        mean_price = df['가격'].mean()
        df = df[(df['가격'] >= mean_price * 0.3) & (df['가격'] <= mean_price * 1.7)]
        df = df.sort_values(by="날짜", ascending=False)

        # ---[추가/수정] 상단에 통계 배치 ---
        st.subheader("📊 시세 요약")
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"""<div style="text-align: center; font-size: 14px; color: gray;">최저가</div>
                        <div style="text-align: center; font-size: 18px; font-weight: bold;">{df['가격'].min():,}원</div>""", unsafe_allow_html=True)
        c2.markdown(f"""<div style="text-align: center; font-size: 14px; color: gray;">평균가</div>
                        <div style="text-align: center; font-size: 24px; font-weight: 800;">{int(df['가격'].mean()):,}원</div>""", unsafe_allow_html=True)
        c3.markdown(f"""<div style="text-align: center; font-size: 14px; color: gray;">최고가</div>
                        <div style="text-align: center; font-size: 18px; font-weight: bold;">{df['가격'].max():,}원</div>""", unsafe_allow_html=True)
        st.divider()
        # -----------------------------------

        # 표시용 데이터
        df_display = df.copy()
        df_display['날짜'] = df_display['날짜'].dt.strftime('%Y-%m-%d')
        df_display['가격'] = df_display['가격'].apply(lambda x: f"{x:,}원")

        # UI 구성: 왼쪽 표, 오른쪽 상세
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader(f"매물 목록 (총 {len(df)}개)")
            event = st.dataframe(df_display[['날짜', '제목', '가격', '작성자']], 
                                 use_container_width=True, on_select="rerun", selection_mode="single-row")

        with col2:
            st.subheader("상세 정보")
            # 선택된 행 인덱스 확인
            if event and len(event["selection"]["rows"]) > 0:
                selected_idx = event["selection"]["rows"][0]
                item = df.iloc[selected_idx]
                st.write(f"### {item['제목']}")
                st.metric("판매 가격", f"{item['가격']:,}원")
                st.write(f"**작성자:** {item['작성자']}")
                st.write(f"**등록일:** {item['날짜'].strftime('%Y-%m-%d')}")
                st.link_button("번개장터 바로가기", f"https://m.bunjang.co.kr/products/{item['pid']}")
            else:
                st.info("목록에서 매물을 선택하면 상세 내용이 표시됩니다.")
    else:
        st.warning("조건에 맞는 매물이 부족합니다.")