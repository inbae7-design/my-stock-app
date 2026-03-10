import streamlit as st
import pandas as pd
import datetime
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

# ==========================================
# 1. 👧 폰 화면에 딱 맞는 모바일 디자인 설정
# ==========================================
st.set_page_config(
    page_title="온유 스케줄 매니저", 
    page_icon="👧",
    layout="wide",
    initial_sidebar_state="collapsed", 
)

st.markdown("""
    <style>
        /* 웹 UI 숨기기 */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container {
            padding-top: 2rem;
            padding-bottom: 0rem;
        }

        /* 전체 배경색 - 따뜻한 파스텔 화이트 */
        .stApp { background-color: #fcf8f3; }
        
        /* 메인 타이틀 */
        h1 {
            color: #26b99a; font-family: 'Malgun Gothic', 'AppleGothic', sans-serif;
            border-bottom: 3px solid #f9f06b; padding-bottom: 10px; font-weight: bold;
        }
        
        /* 📱 스마트폰 맞춤 탭 바 설정 (글자 크기와 여백을 줄여 한 줄에 쏙 들어가게) */
        .stTabs [data-baseweb="tab-list"] {
            border-radius: 15px; background-color: white; padding: 5px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            display: flex; justify-content: space-between; gap: 2px;
        }
        .stTabs [data-baseweb="tab"] {
            font-weight: bold; font-size: 0.9em; color: #333; background-color: #f1f1f1; 
            border-radius: 12px; margin: 0; padding: 8px 10px; transition: 0.3s;
            flex-grow: 1; text-align: center; justify-content: center;
        }
        .stTabs [aria-selected="true"] {
            background-color: #26b99a !important; color: white !important;
        }
        
        /* 카드형 섹션 */
        .onyu-card {
            background-color: white; border-radius: 20px; padding: 15px; 
            margin-bottom: 20px; box-shadow: 0 6px 12px rgba(0,0,0,0.08); 
            border-top-width: 8px; border-top-style: solid; color: #333;
        }
        .home-card { border-top-color: #f7a4a9; }
        .school-card { border-top-color: #89cff0; }
        .academy-card { border-top-color: #f9f06b; }
        
        /* 입력창 및 버튼 */
        .stTextInput input, .stTextArea textarea, .stDateInput div, .stTimeInput div {
            border-radius: 12px; border: 2px solid #e1e1e1; background-color: white; color: black;
        }
        .stButton>button {
            border-radius: 15px; background-color: #26b99a; color: white; font-weight: bold; 
            border: none; padding: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 100%;
        }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# 2. ☁️ 구글 스프레드시트 연결
# ==========================================
@st.cache_resource
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["google_json"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

client = init_connection()

def get_worksheet(title, headers=[]):
    doc = client.open("온유스케줄") 
    try:
        ws = doc.worksheet(title)
    except gspread.exceptions.WorksheetNotFound:
        ws = doc.add_worksheet(title=title, rows="100", cols="10")
        if headers:
            ws.append_row(headers)
    return ws

ws_memo = get_worksheet("메모")
ws_school = get_worksheet("학교", ["날짜"])
ws_academy = get_worksheet("학원", ["학원명", "요일", "시간"])


# ==========================================
# 3. 📱 메인 화면 UI 시작
# ==========================================
st.title("👧 온유 스케줄")

# 💡 탭 이름을 확 줄였습니다!
tab_home, tab_school, tab_academy = st.tabs(["🏠 홈", "🏫 학교", "🎒 학원"])

# --- [탭 1] 홈 화면 ---
with tab_home:
    st.markdown('<div class="onyu-card home-card">', unsafe_allow_html=True)
    st.subheader("오늘의 한 줄 메모 📝")
    current_memo = ws_memo.acell('A1').value if ws_memo.acell('A1').value else "오늘도 즐거운 하루 보내세요! 😊"
    
    with st.form("memo_form"):
        memo_input = st.text_area("가족들에게 남길 메시지:", value=current_memo, height=100)
        if st.form_submit_button("메모 저장하기"):
            ws_memo.update_acell('A1', memo_input)
            st.success("저장 완료!")
            st.rerun() 
    st.markdown('</div>', unsafe_allow_html=True)

# --- [탭 2] 학교 일정 ---
with tab_school:
    st.markdown('<div class="onyu-card school-card">', unsafe_allow_html=True)
    st.subheader("✅ 오늘 학교 다녀왔나요?")
    
    records = ws_school.col_values(1)
    attendance_set = set(records[1:]) if len(records) > 1 else set()
    
    check_date = st.date_input("날짜 선택", datetime.date.today())
    if st.button("🏫 등교 완료! (체크하기)"):
        date_str = check_date.strftime("%Y-%m-%d")
        if date_str not in attendance_set:
            ws_school.append_row([date_str])
            st.success(f"🎉 {date_str} 기록 완료!")
            st.balloons()
            st.rerun()
        else:
            st.warning("이미 체크가 완료된 날짜입니다.")
    st.markdown('</div>', unsafe_allow_html=True)

    if attendance_set:
        sorted_dates = sorted(list(attendance_set), reverse=True)
        display_df = pd.DataFrame({"✅ 학교 간 날짜": sorted_dates})
        display_df.index = range(1, len(display_df) + 1)
        st.dataframe(display_df, use_container_width=True)

# --- [탭 3] 학원 일정 ---
with tab_academy:
    st.markdown('<div class="onyu-card academy-card">', unsafe_allow_html=True)
    st.subheader("📊 온유 학원 시간표")
    
    aca_records = ws_academy.get_all_records()
    if aca_records:
        df_academies = pd.DataFrame(aca_records)
    else:
        df_academies = pd.DataFrame(columns=["학원명", "요일", "시간"])

    st.info("💡 표 안의 글자를 더블 터치해 고치세요.\n\n💡 수정한 뒤 꼭 '저장' 버튼을 눌러주세요.")

    edited_df = st.data_editor(df_academies, num_rows="dynamic", use_container_width=True)
    
    if st.button("💾 구글 시트에 저장"):
        ws_academy.clear()
        data_to_save = [edited_df.columns.values.tolist()] + edited_df.values.tolist()
        ws_academy.update("A1", data_to_save)
        st.success("동기화 완료!")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
