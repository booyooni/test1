import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from utils import load_processed_data, get_product_master, build_content_engine, build_collaborative_clusters, load_external_trends
from recommender import TravelRecommender
from styles import apply_vacation_theme
from analytics import render_logic_explanation, show_deep_eda_v5

# [v5.2.0] Fair & Deep Engine (Keyword Match Analysis)
APP_VERSION = "5.3.0"

# 대시보드 설정
st.set_page_config(page_title="🏝️ HYBRID Travel Dashboard v5.1", layout="wide")
apply_vacation_theme()

# 데이터 로딩 및 엔진 구축
@st.cache_resource(ttl=3600)
def initialize_engine(version):
    df = load_processed_data()
    df = build_collaborative_clusters(df) # 협업 필터링을 위한 클러스터링 선제 수행
    master = get_product_master(df)
    tfidf, cosine_sim = build_content_engine(master)
    
    # [v5.3] 외부 트렌드 데이터 통합 로딩
    external_trends = load_external_trends()
    recommender = TravelRecommender(master, cosine_sim, external_trends=external_trends)
    
    return recommender, master, df

recommender, master, raw_df = initialize_engine(APP_VERSION)

# 세션 상태 관리 (Apply 버튼 기반 UI로 변경)
if 'persona' not in st.session_state:
    st.session_state.persona = {
        'budget_str': '100~200만원',
        'budget': 150,
        'companion': '가족',
        'age': '30대',
        'style': '관광·명소',
        'stay_value': '청결/위생',
        'guide_style': '전문 지식형 (역사 중심)'
    }

if 'applied_persona' not in st.session_state:
    st.session_state.applied_persona = st.session_state.persona.copy()

if 'bookmarks' not in st.session_state:
    st.session_state.bookmarks = []

if 'is_loading' not in st.session_state:
    st.session_state.is_loading = False

# --- [Sidebar: Configuration Panel] ---
with st.sidebar:
    st.markdown("### 🎯 추천 옵션 설정")
    st.markdown("---")

    # 옵션 선택
    budget_options = ["100만원 미만", "100~200만원", "200~300만원", "300만원 이상"]
    selected_budget = st.selectbox(
        "💰 여행 예산",
        budget_options,
        index=budget_options.index(st.session_state.persona.get('budget_str', '100~200만원')),
        key="budget_select"
    )
    st.session_state.persona['budget_str'] = selected_budget
    st.session_state.persona['budget'] = 50 if "100만원 미만" in selected_budget else (150 if "100~200만원" in selected_budget else (250 if "200~300만원" in selected_budget else 350))

    companion_options = ["혼자", "커플·연인", "가족", "친구·지인"]
    selected_companion = st.selectbox(
        "🤝 동행자",
        companion_options,
        index=companion_options.index(st.session_state.persona.get('companion', '가족')),
        key="companion_select"
    )
    st.session_state.persona['companion'] = selected_companion

    age_options = ["20대", "30대", "40대", "50대 이상"]
    selected_age = st.selectbox(
        "🎂 연령대",
        age_options,
        index=age_options.index(st.session_state.persona.get('age', '30대')),
        key="age_select"
    )
    st.session_state.persona['age'] = selected_age

    style_options = ["휴양·힐링", "관광·명소", "미식·맛집", "쇼핑·도심"]
    selected_style = st.selectbox(
        "✈️ 여행 스타일",
        style_options,
        index=style_options.index(st.session_state.persona.get('style', '관광·명소')),
        key="style_select"
    )
    st.session_state.persona['style'] = selected_style

    stay_options = ["청결/위생", "수영장/부대시설", "조식 퀄리티", "접근성/위치"]
    selected_stay = st.selectbox(
        "🏢 숙소 중요도",
        stay_options,
        index=stay_options.index(st.session_state.persona.get('stay_value', '청결/위생')),
        key="stay_select"
    )
    st.session_state.persona['stay_value'] = selected_stay

    guide_options = ["전문 지식형 (역사 중심)", "친근 소통형 (배려 중심)"]
    selected_guide = st.selectbox(
        "🎙️ 가이드 스타일",
        guide_options,
        index=guide_options.index(st.session_state.persona.get('guide_style', '전문 지식형 (역사 중심)')),
        key="guide_select"
    )
    st.session_state.persona['guide_style'] = selected_guide

    st.markdown("---")

    # Apply 버튼
    if st.button("🚀 추천 결과 적용하기", use_container_width=True, type="primary"):
        with st.spinner("🔄 추천 결과를 계산하고 있습니다..."):
            import time
            time.sleep(1)  # 시뮬레이션
            st.session_state.is_loading = True
            st.session_state.applied_persona = st.session_state.persona.copy()
        st.success("✅ 추천 옵션이 적용되었습니다!")
        st.rerun()

    # 북마크 표시
    if st.session_state.bookmarks:
        st.markdown("---")
        st.markdown(f"### 📌 북마크 ({len(st.session_state.bookmarks)}개)")
        for i, bookmark in enumerate(st.session_state.bookmarks):
            st.markdown(f"• {bookmark[:30]}...")

if 'has_seen_guide' not in st.session_state:
    st.session_state.has_seen_guide = False

# 초기 가이드 표시
if not st.session_state.has_seen_guide:
    st.info("💡 **처음 방문하셨나요?**\n\n1. 왼쪽 사이드바에서 여행 옵션을 선택하세요\n2. '🚀 추천 결과 적용하기' 버튼을 클릭하세요\n3. 아래 탭에서 상세한 추천 결과를 확인하세요\n\n북마크 기능으로 마음에 드는 상품을 저장할 수 있습니다!")

    if st.button("✅ 가이드 확인했습니다", key="guide_ack"):
        st.session_state.has_seen_guide = True
        st.rerun()

    st.markdown("---")

# --- [Main Dashboard Overview Section] ---

# --- [Results Section] ---
persona = st.session_state.applied_persona

# 추천 결과 요약 카드
if st.session_state.applied_persona:
    recs = recommender.rule_based_recommend(persona)
    if not recs.empty:
        top_product = recs.iloc[0]
        price_str = f"{top_product['성인가격']:,.0f}원" if not pd.isna(top_product.get('성인가격')) else "가격 별도 문의"

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(0, 123, 255, 0.1)); border: 2px solid #00D4FF; padding: 25px; border-radius: 20px; margin-bottom: 30px;">
            <h3 style="color: #00D4FF; margin-top: 0; margin-bottom: 15px;">🎯 추천 결과 요약</h3>
            <div style="display: flex; gap: 20px; align-items: center; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 200px;">
                    <h4 style="color: #FFFFFF; margin-bottom: 5px;">🏆 TOP 추천 상품</h4>
                    <p style="color: #E0E0E0; margin: 0; font-size: 1.1em;"><b>{top_product['상품명'][:40]}...</b></p>
                    <p style="color: #00D4FF; margin: 5px 0;">💰 {price_str} | ⭐ {top_product['평점']:.1f}</p>
                </div>
                <div style="flex: 1; min-width: 200px;">
                    <h4 style="color: #FFFFFF; margin-bottom: 5px;">📊 추천 통계</h4>
                    <p style="color: #E0E0E0; margin: 0;">총 {len(recs)}개 상품 추천</p>
                    <p style="color: #E0E0E0; margin: 0;">평균 평점: {recs['평점'].mean():.1f}/5.0</p>
                </div>
                <div style="flex: 1; min-width: 200px;">
                    <h4 style="color: #FFFFFF; margin-bottom: 5px;">📌 북마크</h4>
                    <p style="color: #E0E0E0; margin: 0;">저장된 상품: {len(st.session_state.bookmarks)}개</p>
                    <p style="color: #E0E0E0; margin: 0;">아래 상품들에서 💾 버튼을 클릭하세요</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# [v5.0 Summary Header]
st.markdown(f"""
<div style="background: rgba(0, 212, 255, 0.08); border: 2px solid #00D4FF; padding: 35px; border-radius: 25px; margin-bottom: 45px;">
    <h2 style="color: #00D4FF; margin-top: 0; filter: drop-shadow(0 0 10px rgba(0,212,255,0.5));">✨ {persona.get('companion','가족')}과(와) 함께하는 {persona.get('style','미식')} 여행 분석 리포트</h2>
    <div style="display: flex; justify-content: space-between; align-items: center; gap: 30px; margin-top: 25px;">
        <div style="flex: 1; text-align: center; border-right: 1px solid rgba(255,255,255,0.2);">
            <p style="color: #00D4FF; font-weight: 800; font-size: 1.2rem; margin: 0;">{persona.get('budget_str','100~200만원')}</p>
            <small style="color: #FFFFFF; opacity: 0.8;">Budget Level</small>
        </div>
        <div style="flex: 1; text-align: center; border-right: 1px solid rgba(255,255,255,0.2);">
            <p style="color: #00D4FF; font-weight: 800; font-size: 1.2rem; margin: 0;">{persona.get('style','관광')}</p>
            <small style="color: #FFFFFF; opacity: 0.8;">Travel Style</small>
        </div>
        <div style="flex: 1; text-align: center;">
            <p style="color: #00D4FF; font-weight: 800; font-size: 1.2rem; margin: 0;">{persona.get('companion','친구')}</p>
            <small style="color: #FFFFFF; opacity: 0.8;">Companion</small>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🎯 Ranked Recommendation", "🔍 Product Browser", "📊 Analytics Mastery", "🗺️ Destination Map"])

with tab1:
        st.subheader("🎯 v5.5 Integrated Price & Itinerary Engine")
        recs = recommender.rule_based_recommend(persona)
        
        ranks = ["1st", "2nd", "3rd", "4th", "5th"]
        for i, (idx, row) in enumerate(recs.iterrows()):
            with st.container():
                reasons_html = "".join([f"<li style='margin-bottom:10px; color: #FFFFFF;'>• {r}</li>" for r in row.get('reasons', [])])
                price_str = f"{row['성인가격']:,.0f}원" if not pd.isna(row.get('성인가격')) else "가격 별도 문의"
                
                # 상세일정 요약 (처음 200자)
                itinerary_snippet = row.get('상세일정', '일정 정보 준비 중입니다.')
                if isinstance(itinerary_snippet, str) and len(itinerary_snippet) > 200:
                    itinerary_snippet = itinerary_snippet[:200] + "..."
                
                st.markdown(f"""
<div class="product-card" style="position: relative;">
<div class="rank-badge">RANK #{ranks[i]}</div>
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
<span class="badge-{row['대상도시']}">{row['대상도시']}</span>
<div style="color: #00D4FF; font-weight: 900; font-size: 1.5rem;">Match: {row.get('total_score', 0.1):.1f}</div>
</div>
<h2 style="color: #FFFFFF !important; font-size: 1.8rem; margin-bottom: 5px;">{row['상품명']}</h2>
<p style="color: #00D4FF; font-size: 1.4rem; font-weight: 800; margin-bottom: 15px;">💰 판매가: {price_str}</p>
<p style="color: #E0E0E0; font-size: 1.1rem;">⭐⭐⭐⭐⭐ <b>Rate: {row['평점']:.2f}</b> | Shopping: {row['shopping_count']}회</p>
<div style="background: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 15px; margin: 20px 0;">
<h4 style="color: #00D4FF; margin-bottom: 10px;">📅 주요 일정 미리보기</h4>
<p style="color: #CCCCCC; font-size: 0.9rem; line-height: 1.6;">{itinerary_snippet.strip()}</p>
</div>
<div style="background: rgba(0, 212, 255, 0.05); border: 1px solid rgba(0, 212, 255, 0.3); padding: 30px; border-radius: 20px;">
<h4 style="color: #00D4FF; margin-bottom: 15px;">📌 Data Science Evidence (XAI)</h4>
<ul style="list-style: none; padding: 0; margin: 0;">{reasons_html}</ul>
</div>
</div>
""", unsafe_allow_html=True)
                
                # [v5.3] Hybrid Breakdown
                breakdown = row.get('breakdown', {})
                impact_df = pd.DataFrame({
                    'Factor': list(breakdown.keys()),
                    'Impact': list(breakdown.values())
                })
                
                fig = px.bar(impact_df, x='Impact', y='Factor', orientation='h', 
                             template="plotly_dark", color='Factor', 
                             color_discrete_sequence=['#00D4FF', '#007BFF', '#0055FF', '#004080', '#002040'])
                fig.update_layout(height=180, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                  xaxis=dict(showgrid=False, zeroline=False), yaxis=dict(showgrid=False))
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"impact_chart_{i}")
                
                # 사용자 피드백 수집
                col_like, col_dislike, col_bookmark = st.columns(3)
                with col_like:
                    if st.button(f"👍 Like #{ranks[i]}", key=f"like_{i}"):
                        if 'feedback' not in st.session_state:
                            st.session_state.feedback = {}
                        st.session_state.feedback[row['상품코드']] = 'like'
                        st.success(f"#{ranks[i]} 상품을 좋아요로 평가했습니다!")
                with col_dislike:
                    if st.button(f"👎 Dislike #{ranks[i]}", key=f"dislike_{i}"):
                        if 'feedback' not in st.session_state:
                            st.session_state.feedback = {}
                        st.session_state.feedback[row['상품코드']] = 'dislike'
                        st.warning(f"#{ranks[i]} 상품을 싫어요로 평가했습니다!")
                with col_bookmark:
                    is_bookmarked = row['상품명'] in st.session_state.bookmarks
                    button_text = "💾 북마크 해제" if is_bookmarked else "💾 북마크"
                    button_type = "secondary" if is_bookmarked else "primary"
                    if st.button(button_text, key=f"bookmark_{i}", type=button_type):
                        if is_bookmarked:
                            st.session_state.bookmarks.remove(row['상품명'])
                            st.info(f"💾 '{row['상품명'][:20]}...' 북마크가 해제되었습니다.")
                        else:
                            st.session_state.bookmarks.append(row['상품명'])
                            st.success(f"💾 '{row['상품명'][:20]}...' 북마크에 추가되었습니다!")

with tab2:
        st.subheader("🔍 Integrated Discovery & Itinerary Explorer")
        
        # [A] Collaborative Filtering Section (기존 유지)
        cf_recs = recommender.collaborative_recommend(persona, raw_df)
        if not cf_recs.empty:
            st.markdown(f"#### 🤝 취향 유사 고객 추천 ({persona.get('age')} {persona.get('style')})")
            st.info(cf_recs.iloc[0]['cf_reason'])
            
            # 가격 정보가 있으면 표시
            display_cf = cf_recs.copy()
            if '성인가격' in display_cf.columns:
                display_cf['가격'] = display_cf['성인가격'].apply(lambda x: f"{x:,.0f}원" if not pd.isna(x) else "문의")
            
            st.dataframe(
                display_cf[['상품명', '대상도시', '평점', '가격' if '가격' in display_cf.columns else 'price_group']], 
                use_container_width=True, hide_index=True
            )

        st.write("---")
        
        # [B] Content-based Discovery Section
        st.markdown("#### 🔍 상품성 유사 분석 및 상세 일정 확인")
        search_query = st.text_input("상품명 또는 키워드 분석 검색", "", placeholder="예: 나트랑 달랏, 싱가포르 루지...")
        filtered_master = master[master['상품명'].str.contains(search_query, na=False)]
        
        if not filtered_master.empty:
            selected_product_idx = st.selectbox(
                "분석할 상품을 선택하세요:", 
                filtered_master.index, 
                format_func=lambda x: f"[{master.loc[x, '상품코드']}] {master.loc[x, '상품명'][:40]}..."
            )
            target_code = master.loc[selected_product_idx, '상품코드']
            target_row = master.loc[selected_product_idx]
            
            col1, col2 = st.columns([1, 1])
            with col1:
                st.write(f"👉 **'{target_code}' 상품과 상품성이 유사한 추천 목록:**")
                sim_recs = recommender.content_based_recommend(target_code)
                if not sim_recs.empty:
                    if '성인가격' in sim_recs.columns:
                        sim_recs['가격'] = sim_recs['성인가격'].apply(lambda x: f"{x:,.0f}원" if not pd.isna(x) else "문의")
                    st.dataframe(
                        sim_recs[['상품명', '대상도시', '가격' if '가격' in sim_recs.columns else '평점', 'similarity']], 
                        use_container_width=True, hide_index=True
                    )
            
            with col2:
                st.write(f"📅 **선택 상품 상세 일정 ({target_code}):**")
                itinerary_text = target_row.get('상세일정', '일정 데이터가 없습니다.')
                with st.expander("전체 일정 확인하기 (Click)", expanded=True):
                    st.markdown(f"""
                    <div style="background: rgba(0,0,0,0.2); padding: 15px; border-radius: 10px; height: 300px; overflow-y: scroll; font-size: 0.85rem; color: #EEEEEE;">
                        {itinerary_text.replace('\n', '<br>')}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("일치하는 상품이 없습니다. 다른 키워드로 검색해 보세요.")

with tab3:
        st.subheader("📊 Analytics Mastery: Real-world Insights")
        render_logic_explanation()
        st.write("---")
        show_deep_eda_v5(raw_df)

with tab4:
        st.subheader("🗺️ Destination Map: Explore Recommended Locations")
        
        # 도시별 좌표 정의
        city_coords = {
            '나트랑': [12.2388, 109.1967],
            '다낭': [16.0544, 108.2022],
            '싱가포르': [1.3521, 103.8198]
        }
        
        # 추천 상품의 도시별 그룹화
        recs = recommender.rule_based_recommend(persona)
        city_counts = recs['대상도시'].value_counts()
        
        # Folium 지도 생성
        import folium
        from streamlit_folium import st_folium
        
        # 지도 중심을 첫 번째 추천 도시로 설정
        first_city = recs.iloc[0]['대상도시'] if not recs.empty else '나트랑'
        center_lat, center_lon = city_coords.get(first_city, [12.2388, 109.1967])
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles='CartoDB dark_matter')
        
        # 각 도시별 마커 추가
        for city, count in city_counts.items():
            if city in city_coords:
                lat, lon = city_coords[city]
                # 해당 도시의 추천 상품 목록
                city_recs = recs[recs['대상도시'] == city]
                popup_content = f"<b>{city}</b><br>추천 상품: {count}개<br><br>"
                for _, row in city_recs.head(3).iterrows():  # 상위 3개만 표시
                    price_str = f"{row['성인가격']:,.0f}원" if not pd.isna(row.get('성인가격')) else "가격 별도 문의"
                    popup_content += f"• {row['상품명'][:30]}...<br>💰 {price_str}<br>⭐ {row['평점']:.1f}<br><br>"
                
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=f"{city} ({count} recommendations)",
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(m)
        
        # Streamlit에 지도 표시
        st_folium(m, width=700, height=500)

# [Luxury Footer]
st.markdown(f"""
    <div class="footer-container" style="border-top: 2px solid #00D4FF; padding-top: 40px;">
        <span style="color: #00D4FF; font-weight: 800; font-size: 1.1rem;">📑 [Data Science Standards v5.5]</span><br>
        Source: @travel_review_260404 Database & Integrated Price Engine. 실시간 가격 및 상세 일정 데이터 포함.<br><br>
        <span style="color: #00D4FF; font-weight: 800; font-size: 1.1rem;">📈 [Report Analytics Guide]</span><br>
        본 리포트는 실제 판매 데이터와 트렌드 지수를 5:5로 결합한 하이브리드 추천 엔진 v5.5 결과를 기반으로 함.
    </div>
    """, unsafe_allow_html=True)
