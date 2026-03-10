import streamlit as st
import pandas as pd
import datetime

# --- 1. 페이지 기본 설정 (항상 최상단에 위치) ---
st.set_page_config(page_title="온유 일정 관리", layout="wide", page_icon="📱")

# --- 2. 모바일 앱 느낌을 위한 웹사이트 흔적 지우기 ---
hide_web_ui = """
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
.block-container {
    padding-top: 2rem;
    padding-bottom: 0rem;
}
</style>
"""
st.markdown(hide_web_ui, unsafe_allow_html=True)

# ==========================================
# 3. 구글 스프레드시트 연동 (어제 완성하신 부분)
# ==========================================
# ※ 주의: 어제 사용하신 구글 시트 라이브러리(st.connection 등)에 맞춰 
# 데이터를 불러오고 저장하는 코드로 일부 수정해서 사용해 주세요.
from streamlit_gsheets import GSheetsConnection

# 시트 연결 객체 생성
conn = st.connection("gsheets", type=GSheetsConnection)

# 데이터 불러오기 (예시: '출석' 워크시트와 '학원' 워크시트)
try:
    df_attendance = conn.read(worksheet="출석", usecols=[0], ttl=5)
    attendance_list = df_attendance.iloc[:, 0].dropna().tolist() if not df_attendance.empty else []
except Exception:
    attendance_list = []

try:
    df_academies = conn.read(worksheet="학원", usecols=[0, 1, 2], ttl=5)
    if df_academies.empty:
        df_academies = pd.DataFrame(columns=["학원명", "요일", "시간"])
except Exception:
    df_academies = pd.DataFrame(columns=["학원명", "요일", "시간"])

# ==========================================
# 4. 사이드바: 메인 메뉴 구성
# ==========================================
st.sidebar.title("📌 메인 메뉴")
menu = st.sidebar.radio("이동할 페이지를 선택하세요:", ["🏠 홈", "👧 아이 일정"])
st.sidebar.markdown("---")

# ==========================================
# 5. 화면 렌더링
# ==========================================
if menu == "🏠 홈":
    st.title("환영합니다! ✨")
    st.markdown("""
    ### 온유를 위한 전용 대시보드입니다.
    화면 좌측 상단의 메뉴(☰) 버튼을 눌러 일정을 관리해 보세요.
    
    * **👧 아이 일정:** 학교 등하교 체크 및 학원 시간표 관리
    """)

elif menu == "👧 아이 일정":
    st.title("👧 온유 일정 관리")
    
    tab1, tab2 = st.tabs(["🏫 1. 학교 일정 (등하교 체크)", "🎒 2. 학원 일정 (스케쥴표)"])
    
    # --- 하위 메뉴 1: 학교 일정 ---
    with tab1:
        st.subheader("✅ 오늘 학교에 잘 다녀왔나요?")
        
        col_date, col_btn = st.columns([1, 1])
        with col_date:
            check_date = st.date_input("날짜 선택", datetime.date.today())
        with col_btn:
            st.write("") 
            st.write("")
            if st.button("🏫 등교 완료! (체크하기)", use_container_width=True):
                date_str = check_date.strftime("%Y-%m-%d")
                
                if date_str not in attendance_list:
                    attendance_list.append(date_str)
                    
                    # 구글 시트 '출석' 워크시트에 업데이트 저장
                    updated_df = pd.DataFrame({"✅ 학교 간 날짜": attendance_list})
                    conn.update(worksheet="출석", data=updated_df)
                    
                    st.success(f"🎉 {date_str} - 등교 기록이 구글 시트에 저장되었습니다!")
                    st.balloons() 
                else:
                    st.warning("이미 체크가 완료된 날짜입니다.")
        
        st.markdown("---")
        st.subheader("🗓️ 등교 완료 기록")
        if attendance_list:
            sorted_dates = sorted(attendance_list, reverse=True)
            display_df = pd.DataFrame({"✅ 학교 간 날짜": sorted_dates})
            display_df.index = range(1, len(display_df) + 1) 
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("아직 체크된 등교 기록이 없습니다.")

    # --- 하위 메뉴 2: 학원 일정 ---
    with tab2:
        st.subheader("🎒 다니는 학원 추가하기")
        
        with st.form("academy_form", clear_on_submit=True):
            col_name, col_days, col_time = st.columns([2, 3, 2])
            with col_name:
                aca_name = st.text_input("학원 이름 (예: 피아노, 영어)")
            with col_days:
                aca_days = st.multiselect("요일 선택", ["월", "화", "수", "목", "금", "토", "일"])
            with col_time:
                aca_time = st.time_input("시간", datetime.time(14, 0)) 
                
            submit_aca = st.form_submit_button("학원 스케쥴 추가")
            
            if submit_aca:
                if aca_name and aca_days:
                    new_row = pd.DataFrame({
                        "학원명": [aca_name],
                        "요일": [", ".join(aca_days)],
                        "시간": [aca_time.strftime("%H:%M")]
                    })
                    # 기존 데이터에 새 일정 추가 후 구글 시트에 저장
                    df_academies = pd.concat([df_academies, new_row], ignore_index=True)
                    conn.update(worksheet="학원", data=df_academies)
                    
                    st.success(f"{aca_name} 일정이 구글 시트에 추가되었습니다!")
                else:
                    st.error("학원 이름과 요일을 모두 입력해 주세요.")
                    
        st.markdown("---")
        
        st.subheader("📊 온유의 주간 학원 시간표 (직접 수정 가능)")
        st.info("💡 **수정/삭제:** 표를 더블클릭하여 내용을 고치거나, 행을 선택해 지운 뒤 아래의 '구글 시트에 변경사항 저장' 버튼을 누르세요.")
        
        # 편집 가능한 데이터프레임
        edited_df = st.data_editor(df_academies, num_rows="dynamic", use_container_width=True)
        
        # 변경사항 수동 저장 버튼 (데이터 동기화 안정성을 위해 추가)
        if st.button("💾 구글 시트에 변경사항 저장", use_container_width=True):
            conn.update(worksheet="학원", data=edited_df)
            st.success("학원 시간표가 성공적으로 동기화되었습니다!")
