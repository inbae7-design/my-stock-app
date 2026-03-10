# --- 페이지 기본 설정 ---
st.set_page_config(page_title="나만의 대시보드", layout="wide", page_icon="📱")

# --- [추가된 부분] 모바일 앱 느낌을 위한 웹사이트 흔적 지우기 ---
hide_web_ui = """
    <style>
    #MainMenu {visibility: hidden;} /* 우측 상단 햄버거 메뉴 숨기기 */
    header {visibility: hidden;} /* 상단 빈 공간(헤더) 숨기기 */
    footer {visibility: hidden;} /* 하단 'Made with Streamlit' 숨기기 */
    .block-container {
        padding-top: 2rem; /* 상단 여백 줄이기 */
        padding-bottom: 0rem; /* 하단 여백 줄이기 */
    }
    </style>
    """
st.markdown(hide_web_ui, unsafe_allow_html=True)
# -----------------------------------------------------------

# --- 한글 폰트 설정 --- (이하 기존 코드와 동일)import streamlit as st
import pandas as pd
import datetime
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

# ==========================================
# 👧 초등학생 맞춤 활기찬 모바일 디자인 설정
# ==========================================
st.set_page_config(
    page_title="온유 스케줄 매니저", 
    page_icon="👧",
    initial_sidebar_state="collapsed", # 모바일은 사이드바 닫기
)

# --- 커스텀 CSS (세련된Elementary 스타일) ---
st.markdown("""
    <style>
        /* 전체 배경색 - 따뜻한 파스텔 화이트 */
        .stApp {
            background-color: #fcf8f3;
        }
        
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
            border-radius: 15px;
            background-color: white;
            padding: 5px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stTabs [data-baseweb="tab"] {
            font-weight: bold;
            font-size: 1.1em;
            color: #333;
            background-color: #f1f1f1;
            border-radius: 12px;
            margin: 0 5px;
            padding: 10px 15px;
            transition: 0.3s;
        }
        .stTabs [aria-selected="true"] {
            background-color: #26b99a !important; /* 선택 시 민트색 */
            color: white !important;
        }
        
        /* 카드형 섹션 (Home, School, Academy 다르게) */
        .onyu-card {
            background-color: white;
            border-radius: 20px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 6px 12px rgba(0,0,0,0.08);
            border-top-width: 8px; /* 상단 포인트 컬러 */
            border-top-style: solid;
        }
        .home-card { border-top-color: #f7a4a9; } /* 핑크 */
        .school-card { border-top-color: #89cff0; } /* 스카이 블루 */
        .academy-card { border-top-color: #f9f06b; } /* 옐로우 */
        
        /* 입력창 디자인 - 둥글게 */
        .stTextInput input, .stTextArea textarea, .stDateInput div, .stTimeInput div {
            border-radius: 12px;
            border: 2px solid #e1e1e1;
        }
        .stTextInput input:focus, .stTextArea textarea:focus, .stDateInput div:focus, .stTimeInput div:focus {
            border-color: #26b99a;
            box-shadow: 0 0 5px rgba(38, 185, 154, 0.3);
        }
        
        /* 버튼 디자인 - 활기찬 민트 & 둥글게 */
        .stButton>button {
            border-radius: 15px;
            background-color: #26b99a;
            color: white;
            font-weight: bold;
            border: none;
            padding: 12px 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: #21a187;
            box-shadow: 0 6px 10px rgba(0,0,0,0.15);
        }
        
        /* 데이터 편집기 (학원 시간표) */
        [data-testid="stDataEditor"] {
            background-color: white;
            border-radius: 15px;
            overflow: hidden;
            border: 2px solid #e1e1e1;
        }
        /* 테이블 헤더 컬러 */
        [data-testid="stDataEditor"] div[role="columnheader"] {
            background-color: #e6faf6;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# ☁️ 구글 스프레드시트 연결 및 초기 세팅
# ==========================================
@st.cache_resource
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["google_json"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

try:
    client = init_connection()
    # 내 구글 드라이브에 만든 엑셀 파일 이름과 정확히 일치해야 합니다.
    sheet = client.open("온유스케줄") 
except Exception as e:
    st.error("⚠️ 구글 스프레드시트 연결 실패! 파일 이름('온유스케줄')이 맞는지, 로봇 이메일을 '편집자'로 공유했는지 다시 확인해주세요.")
    st.stop()

# --- 엑셀 안의 하위 시트(탭) 자동으로 만들기 ---
def get_worksheet(title, headers=[]):
    try:
        ws = sheet.worksheet(title)
    except gspread.exceptions.WorksheetNotFound:
        # 시트가 없으면 앱이 알아서 새로 만듭니다.
        ws = sheet.add_worksheet(title=title, rows="100", cols="20")
        if headers:
            ws.append_row(headers)
    return ws

# 3개의 하위 시트 준비
ws_memo = get_worksheet("메모")
ws_school = get_worksheet("학교", ["날짜"])
ws_academy = get_worksheet("학원", ["학원명", "요일", "시간"])


# ==========================================
# 📱 메인 화면 UI 시작
# ==========================================
st.title("👧 온유 스케줄 매니저")
st.markdown("구글 시트에 영구 저장되는 온유만의 전용 앱! ☁️")

# 모바일 터치 최적화 상단 탭 (Vibrant & Elegant 스타일)
tab_home, tab_school, tab_academy = st.tabs(["🏠 홈", "🏫 학교 기록", "🎒 학원 시간표"])

# --- 1. 홈 화면 (메모장 -> 구글 시트 연동) ---
with tab_home:
    st.markdown('<div class="onyu-card home-card">', unsafe_allow_html=True)
    
    st.subheader("오늘의 한 줄 메모 📝")
    # 구글 시트의 A1 셀 값 읽어오기
    current_memo = ws_memo.acell('A1').value if ws_memo.acell('A1').value else "오늘도 즐거운 하루 보내세요! 😊"
    
    with st.form("memo_form"):
        memo_input = st.text_area("메모장", value=current_memo, height=150, label_visibility="collapsed")
        if st.form_submit_button("메모 구글에 저장하기", use_container_width=True):
            ws_memo.update_acell('A1', memo_input)
            st.success("구글 시트에 메모가 안전하게 저장되었습니다!")
            st.rerun() # 화면 새로고침
            
    st.markdown('</div>', unsafe_allow_html=True)

# --- 2. 학교 일정 (출석 기록 -> 구글 시트 연동) ---
with tab_school:
    st.markdown('<div class="onyu-card school-card">', unsafe_allow_html=True)
    
    st.subheader("✅ 오늘 학교 다녀왔나요?")
    # 구글 시트의 A열 데이터를 모두 읽어옵니다 (첫 줄 '날짜' 제목 제외)
    records = ws_school.col_values(1)[1:] 
    attendance_set = set(records)
    
    check_date = st.date_input("날짜 선택", datetime.date.today())
    
    if st.button("🏫 등교 완료! (구글 시트에 기록)", use_container_width=True):
        date_str = check_date.strftime("%Y-%m-%d")
        if date_str not in attendance_set:
            ws_school.append_row([date_str]) # 구글 시트 맨 아랫줄에 날짜 추가
            st.success(f"🎉 {date_str} - 출석 기록이 구글에 저장되었습니다!")
            st.balloons()
            st.rerun()
        else:
            st.warning("이미 체크가 완료된 날짜입니다.")
            
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('---')
    st.subheader("🗓️ 전체 등교 기록")
    if records:
        sorted_dates = sorted(records, reverse=True)
        df_attendance = pd.DataFrame({"✅ 학교 간 날짜": sorted_dates})
        df_attendance.index = range(1, len(df_attendance) + 1)
        st.dataframe(df_attendance, use_container_width=True)
    else:
        st.info("아직 구글 시트에 기록된 데이터가 없습니다.")

# --- 3. 학원 일정 (시간표 관리 -> 구글 시트 연동) ---
with tab_academy:
    st.markdown('<div class="onyu-card academy-card">', unsafe_allow_html=True)
    
    st.subheader("📊 온유 학원 시간표")
    # 구글 시트에서 전체 시간표 데이터 읽어오기
    aca_records = ws_academy.get_all_records()
    if aca_records:
        df_academies = pd.DataFrame(aca_records)
    else:
        df_academies = pd.DataFrame(columns=["학원명", "요일", "시간"])
        
    st.info("💡 **수정/삭제:** 표 안의 글자를 더블 터치해 고치거나, 왼쪽 체크박스를 누르고 쓰레기통 아이콘을 누르세요.\n\n💡 **저장 필수:** 표를 수정한 뒤 반드시 아래의 파란색 저장 버튼을 눌러야 구글에 반영됩니다.")
    
    # 편집 가능한 표 (새 행 추가/삭제 모두 지원)
    edited_df = st.data_editor(df_academies, num_rows="dynamic", use_container_width=True)
    
    if st.button("💾 수정한 시간표 구글에 덮어쓰기", use_container_width=True):
        # 1. 시트를 싹 비우기
        ws_academy.clear()
        
        # 2. 수정된 표의 제목과 데이터를 리스트로 변환
        headers = edited_df.columns.tolist()
        data = edited_df.fillna("").values.tolist()
        
        # 3. 구글 시트에 한 번에 덮어쓰기
        if data:
            ws_academy.update(values=[headers] + data, range_name="A1")
        else:
            ws_academy.append_row(headers) # 데이터가 다 지워졌을 땐 헤더만 남기기
            
        st.success("시간표가 구글 시트와 완벽하게 동기화되었습니다!")
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)

