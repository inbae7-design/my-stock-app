import streamlit as st
import pandas as pd
import datetime

# --- 페이지 기본 설정 (모바일 최적화를 위해 layout="wide" 제거) ---
st.set_page_config(page_title="온유 스케줄 매니저", page_icon="👧")

# --- 세션 상태 초기화 ---
if 'attendance' not in st.session_state:
    st.session_state.attendance = set() 
if 'academies' not in st.session_state:
    st.session_state.academies = [] 
if 'memo' not in st.session_state:
    st.session_state.memo = "오늘도 즐거운 하루 보내세요! 😊"

# --- 메인 타이틀 ---
st.title("👧 온유 스케줄 매니저")
st.markdown("스마트폰에서 온유의 일정을 쉽고 빠르게 관리하세요!")

# --- [모바일 최적화] 사이드바 대신 상단 탭(Tab) 사용 ---
tab_home, tab_school, tab_academy = st.tabs(["🏠 홈", "🏫 등하교 체크", "🎒 학원 시간표"])

# ==========================================
# 1. 홈 화면 (간단한 메모장 기능 추가)
# ==========================================
with tab_home:
    st.subheader("오늘의 한 줄 메모 📝")
    st.caption("잊지 말아야 할 준비물이나 일정을 적어두세요.")
    
    memo_input = st.text_area("메모장", value=st.session_state.memo, height=150, label_visibility="collapsed")
    
    if st.button("메모 저장하기", use_container_width=True):
        st.session_state.memo = memo_input
        st.success("메모가 저장되었습니다!")

# ==========================================
# 2. 학교 일정 (등하교 체크)
# ==========================================
with tab_school:
    st.subheader("✅ 오늘 학교 다녀왔나요?")
    
    # 모바일은 가로폭이 좁으므로 좌우 배치(columns) 대신 위아래로 시원하게 배치
    check_date = st.date_input("날짜 선택", datetime.date.today())
    
    if st.button("🏫 등교 완료! (체크하기)", use_container_width=True):
        date_str = check_date.strftime("%Y-%m-%d")
        if date_str not in st.session_state.attendance:
            st.session_state.attendance.add(date_str)
            st.success(f"🎉 {date_str} - 출석 기록 완료!")
            st.balloons() 
        else:
            st.warning("이미 체크가 완료된 날짜입니다.")
    
    st.markdown("---")
    st.subheader("🗓️ 최근 등교 기록")
    if st.session_state.attendance:
        sorted_dates = sorted(list(st.session_state.attendance), reverse=True)
        df_attendance = pd.DataFrame({"✅ 학교 간 날짜": sorted_dates})
        df_attendance.index = range(1, len(df_attendance) + 1) 
        st.dataframe(df_attendance, use_container_width=True)
    else:
        st.info("아직 체크된 등교 기록이 없습니다.")

# ==========================================
# 3. 학원 일정 (수정/삭제 가능)
# ==========================================
with tab_academy:
    st.subheader("📊 온유 학원 시간표")
    
    # [모바일 최적화] 입력창이 공간을 많이 차지하지 않도록 접었다 펼칠 수 있는 Expander 사용
    with st.expander("➕ 새 학원 등록하기 (터치하여 열기)"):
        with st.form("academy_form", clear_on_submit=True):
            aca_name = st.text_input("학원 이름 (예: 피아노)")
            aca_days = st.multiselect("요일 선택", ["월", "화", "수", "목", "금", "토", "일"])
            aca_time = st.time_input("시간", datetime.time(14, 0)) 
                
            submit_aca = st.form_submit_button("시간표에 추가", use_container_width=True)
            
            if submit_aca:
                if aca_name and aca_days:
                    st.session_state.academies.append({
                        "학원명": aca_name,
                        "요일": ", ".join(aca_days),
                        "시간": aca_time.strftime("%H:%M")
                    })
                    st.success(f"{aca_name} 추가 완료!")
                else:
                    st.error("학원 이름과 요일을 모두 입력해 주세요.")
                    
    st.markdown("---")
    st.caption("💡 표 안의 글자를 터치하면 수정 가능! 지우려면 왼쪽 체크박스 선택 후 쓰레기통 아이콘 터치")
    
    if st.session_state.academies:
        df_academies = pd.DataFrame(st.session_state.academies)
    else:
        df_academies = pd.DataFrame(columns=["학원명", "요일", "시간"])
        
    edited_df = st.data_editor(df_academies, num_rows="dynamic", use_container_width=True)
    st.session_state.academies = edited_df.to_dict('records')
