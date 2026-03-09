import streamlit as st
import pandas as pd
import datetime
import gspread
import json  # 👈 TOML 에러를 우회하기 위해 추가된 라이브러리
from oauth2client.service_account import ServiceAccountCredentials

# --- 페이지 기본 설정 (모바일 최적화) ---
st.set_page_config(page_title="온유 스케줄 매니저", page_icon="👧")

# ==========================================
# ☁️ 구글 스프레드시트 연결 및 초기 세팅
# ==========================================
@st.cache_resource
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # 비밀 금고(Secrets)에 통째로 넣은 JSON 텍스트를 파이썬 딕셔너리로 변환
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
st.markdown("데이터가 구글 시트에 실시간으로 영구 저장됩니다! ☁️")

# 모바일에서 터치하기 편한 상단 탭 방식
tab_home, tab_school, tab_academy = st.tabs(["🏠 홈", "🏫 학교 기록", "🎒 학원 시간표"])

# --- 1. 홈 화면 (메모장 -> 구글 시트 연동) ---
with tab_home:
    st.subheader("오늘의 한 줄 메모 📝")
    
    # 구글 시트의 A1 셀 값 읽어오기
    current_memo = ws_memo.acell('A1').value if ws_memo.acell('A1').value else "오늘도 즐거운 하루 보내세요! 😊"
    
    with st.form("memo_form"):
        memo_input = st.text_area("메모장", value=current_memo, height=150, label_visibility="collapsed")
        if st.form_submit_button("메모 구글에 저장하기", use_container_width=True):
            ws_memo.update_acell('A1', memo_input)
            st.success("구글 시트에 메모가 안전하게 저장되었습니다!")
            st.rerun() # 화면 새로고침

# --- 2. 학교 일정 (출석 기록 -> 구글 시트 연동) ---
with tab_school:
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
    
    st.markdown("---")
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
    st.subheader("📊 온유 학원 시간표")
    
    # 구글 시트에서 전체 시간표 데이터 읽어오기
    aca_records = ws_academy.get_all_records()
    if aca_records:
        df_academies = pd.DataFrame(aca_records)
    else:
        df_academies = pd.DataFrame(columns=["학원명", "요일", "시간"])
        
    st.info("💡 **수정/삭제:** 표 안의 글자를 터치해 고치거나, 왼쪽 체크박스를 누르고 쓰레기통 아이콘을 누르세요.\n\n💡 **저장 필수:** 표를 수정한 뒤 반드시 아래의 파란색 저장 버튼을 눌러야 구글에 반영됩니다.")
    
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
