import streamlit as st
import pandas as pd
import datetime
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

# ==========================================
# 1. 👧 초등학생 맞춤 활기찬 모바일 디자인 설정
# ==========================================
st.set_page_config(
    page_title="온유 스케줄 매니저", 
    page_icon="👧",
    layout="wide",
    initial_sidebar_state="collapsed", # 모바일 최적화: 사이드바 닫기
)

# 모바일 앱 느낌을 위한 웹사이트 흔적 지우기 & 커스텀 CSS
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
        
        /* 메인 타이틀 - 활기찬 민트 그린 & 둥근 폰트 */
        h1 {
            color: #26b99a; 
            font-family: 'Malgun Gothic', 'AppleGothic', sans-serif;
            border-bottom: 3px solid #f9f06b; /* 하단 노란 포인트 */
            padding-bottom: 10px;
            font-weight: bold;
        }
        
        /* 탭 바 설정 - 둥글고 활기찬 컬러 */
        .stTabs [data-baseweb="tab-list"] {
            border-radius: 15px; background-color: white; padding: 5px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stTabs [data-baseweb="tab"] {
            font-weight: bold; font-size: 1.1em; color: #333; background-color: #f1f1f1; 
            border-radius: 12px; margin: 0 5px; padding: 10px 15px; transition: 0.3s;
        }
        .stTabs [aria-selected="true"] {
            background-color: #26b99a !important; /* 선택 시 민트색 */
            color: white !important;
        }
        
        /* 카드형 섹션 (Home, School, Academy 다르게) */
        .onyu-card {
            background-color: white; border-radius: 20px; padding: 20px; 
            margin-bottom: 20px; box-shadow: 0 6px 12px rgba(0,0,0,0.08); 
            border-top-width: 8px; border-top-style: solid;
        }
        .home-card { border-top-color: #f7a4a9; } /* 핑크 */
        .school-card { border-top-color: #89cff0; } /* 스카이 블루 */
        .academy-card { border-top-color: #f9f06b; } /* 옐로우 */
        
        /* 입력창 및 버튼 디자인 */
        .stTextInput input, .stTextArea textarea, .stDateInput div, .stTimeInput div {
            border-radius: 12px; border: 2px solid #e1e1e1;
        }
        .stTextInput input:focus, .stTextArea textarea:focus, .stDateInput div:focus, .stTimeInput div:focus {
            border-color: #26b99a; box-shadow: 0 0 5px rgba(38, 185, 154, 0.3);
        }
        .stButton>button {
            border-radius: 15px; background-color: #26b99a; color: white; font-weight: bold; 
            border: none; padding: 12px 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: #21a187; box-shadow: 0 6px 10px rgba(0,0,0,0.15);
        }
        
        /* 데이터 편집기 (학원 시간표) */
        [data-testid="stDataEditor"] {
            background-color: white; border-radius: 15px; overflow: hidden; border: 2px solid #e1e1e1;
        }
        [data-testid="stDataEditor"] div[role="columnheader"] {
            background-color: #e6faf6; font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# 2. ☁️ 구글 스프레드시트 연결 및 초기 세팅
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
    # 시트 이름이 다를 경우 아래 "온유 스케줄 매니저"를 어제 만드신 구글 시트 파일명으로 바꿔주세요.
    doc = client.open("온유 스케줄 매니저") 
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
st.title("👧 온유 스케줄 매니저")
st.markdown("데이터가 구글 시트에 실시간으로 영구 저장됩니다! ☁️")

# 모바일 터치 최적화 상단 탭 (Vibrant & Elegant 스타일)
tab_home, tab_school, tab_academy = st.tabs(["🏠 홈", "🏫 학교 기록", "🎒 학원 시간표"])

# --- [탭 1] 홈 화면 (메모장) ---
with tab_home:
    st.markdown('<div class="onyu-card home-card">', unsafe_allow_html=True)
    st.subheader("오늘의 한 줄 메모 📝")
    
    # 구글 시트의 A1 셀 값 읽어오기
    current_memo = ws_memo.acell('A1').value if ws_memo.acell('A1').value else "오늘도 즐거운 하루 보내세요! 😊"
    
    with st.form("memo_form"):
        memo_input = st.text_area("가족들에게 남길 메시지를 적어주세요:", value=current_memo, height=100)
        if st.form_submit_button("메모 저장하기", use_container_width=True):
            ws_memo.update_acell('A1', memo_input)
            st.success("구글 시트에 메모가 안전하게 저장되었습니다!")
            st.rerun() 
            
    st.markdown('</div>', unsafe_allow_html=True)

# --- [탭 2] 학교 일정 (출석 기록) ---
with tab_school:
    st.markdown('<div class="onyu-card school-card">', unsafe_allow_html=True)
    st.subheader("✅ 오늘 학교 다녀왔나요?")
    
    records = ws_school.col_values(1)
    attendance_set = set(records[1:]) if len(records) > 1 else set()
    
    col_date, col_btn = st.columns([1, 1])
    with col_date:
        check_date = st.date_input("날짜 선택", datetime.date.today())
    with col_btn:
        st.write("")
        st.write("")
        if st.button("🏫 등교 완료! (체크하기)", use_container_width=True):
            date_str = check_date.strftime("%Y-%m-%d")
            if date_str not in attendance_set:
                ws_school.append_row([date_str])
                st.success(f"🎉 {date_str} 기록 완료!")
                st.balloons()
                st.rerun()
            else:
                st.warning("이미 체크가 완료된 날짜입니다.")
            
    st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("🗓️ 전체 등교 기록")
    if attendance_set:
        sorted_dates = sorted(list(attendance_set), reverse=True)
        display_df = pd.DataFrame({"✅ 학교 간 날짜": sorted_dates})
        display_df.index = range(1, len(display_df) + 1)
        st.dataframe(display_df, use_container_width=True)

# --- [탭 3] 학원 일정 (시간표 관리) ---
with tab_academy:
    st.markdown('<div class="onyu-card academy-card">', unsafe_allow_html=True)
    st.subheader("📊 온유 학원 시간표")
    
    aca_records = ws_academy.get_all_records()
    if aca_records:
        df_academies = pd.DataFrame(aca_records)
    else:
        df_academies = pd.DataFrame(columns=["학원명", "요일", "시간"])

    st.info("💡 **수정/삭제:** 표 안의 글자를 더블 터치해 고치거나, 왼쪽 상자를 누르고 쓰레기통 아이콘을 누르세요.\n\n💡 **저장 필수:** 표를 수정한 뒤 반드시 아래의 저장 버튼을 눌러야 구글에 반영됩니다.")

    edited_df = st.data_editor(df_academies, num_rows="dynamic", use_container_width=True)
    
    if st.button("💾 구글 시트에 변경사항 저장", use_container_width=True):
        ws_academy.clear()
        # 헤더와 데이터를 리스트 형태로 묶어서 업데이트
        data_to_save = [edited_df.columns.values.tolist()] + edited_df.values.tolist()
        ws_academy.update("A1", data_to_save)
        
        st.success("시간표가 구글 시트와 완벽하게 동기화되었습니다!")
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)
