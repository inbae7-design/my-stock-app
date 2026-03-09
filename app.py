import streamlit as st
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import FinanceDataReader as fdr
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker_module
import platform
import datetime

# --- 페이지 기본 설정 ---
st.set_page_config(page_title="나만의 개인 대시보드", layout="wide", page_icon="✨")

# --- 한글 폰트 설정 ---
if platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
elif platform.system() == 'Darwin':
    plt.rcParams['font.family'] = 'AppleGothic'
else:
    plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False

# --- 세션 상태(Session State) 초기화 ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
    
if 'attendance' not in st.session_state:
    st.session_state.attendance = set() 
if 'academies' not in st.session_state:
    st.session_state.academies = [] 

# --- 공통 함수 ---
@st.cache_data
def load_krx_data():
    try:
        return fdr.StockListing('KRX')
    except Exception:
        return pd.DataFrame(columns=['Name', 'Code', 'Market'])

def get_ticker_from_name(name, krx_df):
    if name.encode().isalpha():
        return name.upper()
    if not krx_df.empty:
        match = krx_df[krx_df['Name'] == name]
        if not match.empty:
            code = match.iloc[0]['Code']
            market = match.iloc[0]['Market']
            return f"{code}.KS" if 'KOSPI' in market else f"{code}.KQ"
    return name

# ==========================================
# 사이드바: 메인 메뉴 구성
# ==========================================
st.sidebar.title("📌 메인 메뉴")
menu = st.sidebar.radio("이동할 페이지를 선택하세요:", ["🏠 홈", "📈 주식 차트", "👧 아이 일정"])
st.sidebar.markdown("---")

# ==========================================
# 1. 홈 화면 (Home)
# ==========================================
if menu == "🏠 홈":
    st.title("환영합니다! ✨")
    st.markdown("""
    ### 나만의 웹 대시보드에 오신 것을 환영합니다.
    좌측 메뉴를 선택하여 원하는 기능을 이용해 보세요.
    
    * **📈 주식 차트:** 한국/미국 주식 검색 및 프로급 차트 (MACD, RSI 지원)
    * **👧 아이 일정:** 온유의 학교 등하교 체크 및 학원 시간표 관리
    """)

# ==========================================
# 2. 주식 차트 메뉴 (Stock)
# ==========================================
elif menu == "📈 주식 차트":
    st.title("📈 프로급 실시간 주식 차트")
    
    st.sidebar.subheader("⚙️ 차트 설정")
    show_macd = st.sidebar.checkbox("MACD 보조지표 켜기", value=False)
    show_rsi = st.sidebar.checkbox("RSI 보조지표 켜기", value=False)
    
    st.sidebar.subheader("🕒 최근 검색")
    for item in st.session_state.history:
        if st.sidebar.button(item, key=f"btn_{item}"):
            st.session_state.search_query = item

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search_input = st.text_input("회사명 또는 종목코드 (예: 삼성전자, AAPL)", value=st.session_state.search_query)
    with col2:
        interval = st.selectbox("시간 간격", ["1m", "1h", "1d", "1wk", "1mo"], index=2)
    with col3:
        st.write("") 
        st.write("")
        search_btn = st.button("차트 그리기", use_container_width=True)

    if search_btn or search_input:
        if search_input:
            if search_input in st.session_state.history:
                st.session_state.history.remove(search_input)
            st.session_state.history.insert(0, search_input)
            st.session_state.history = st.session_state.history[:10]

            krx_df = load_krx_data()
            if krx_df.empty and not search_input.encode().isalpha():
                st.warning("⚠️ 현재 클라우드 서버 보안 문제로 한글 검색이 제한되어 있습니다. 종목 코드를 입력해 주세요.")

            ticker = get_ticker_from_name(search_input, krx_df)
            period_map = {'1m': '7d', '1h': '730d', '1d': '5y', '1wk': '5y', '1mo': '10y'}
            period = period_map.get(interval, '1y')

            with st.spinner('데이터를 분석하고 차트를 그리는 중입니다...'):
                try:
                    df = yf.download(ticker, period=period, interval=interval)
                    
                    if df.empty:
                        st.error("데이터를 찾을 수 없습니다. 회사명이나 종목 코드를 확인해 주세요.")
                    else:
                        if isinstance(df.columns, pd.MultiIndex):
                            df.columns = df.columns.droplevel(1)

                        delta = df['Close'].diff()
                        up = delta.clip(lower=0)
                        down = -1 * delta.clip(upper=0)
                        ema_up = up.ewm(com=13, adjust=False).mean()
                        ema_down = down.ewm(com=13, adjust=False).mean()
                        rs = ema_up / ema_down
                        df['RSI'] = 100 - (100 / (1 + rs))

                        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
                        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
                        df['MACD'] = exp1 - exp2
                        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
                        df['MACD_Hist'] = df['MACD'] - df['Signal']

                        apds = []
                        panel_ratios = [3, 1] 
                        current_panel = 2     

                        if show_macd:
                            apds.append(mpf.make_addplot(df['MACD'], panel=current_panel, color='fuchsia', secondary_y=False))
                            apds.append(mpf.make_addplot(df['Signal'], panel=current_panel, color='b', secondary_y=False))
                            apds.append(mpf.make_addplot(df['MACD_Hist'], type='bar', panel=current_panel, color='dimgray', secondary_y=False))
                            panel_ratios.append(1) 
                            current_panel += 1

                        if show_rsi:
                            apds.append(mpf.make_addplot(df['RSI'], panel=current_panel, color='purple', ylabel='RSI', secondary_y=False))
                            apds.append(mpf.make_addplot([70]*len(df), panel=current_panel, color='r', linestyle='dashed', secondary_y=False))
                            apds.append(mpf.make_addplot([30]*len(df), panel=current_panel, color='b', linestyle='dashed', secondary_y=False))
                            panel_ratios.append(1) 
                            current_panel += 1

                        dt_format = '%y-%m-%d %H:%M' if interval in ['1m', '1h'] else '%Y-%m-%d'
                        mc = mpf.make_marketcolors(up='red', down='blue', edge='inherit', wick='inherit', volume='inherit')
                        korean_style = mpf.make_mpf_style(marketcolors=mc, gridstyle='--')

                        fig_height = 7 + (current_panel - 2) * 2.5
                        fig, axes = mpf.plot(df, type='candle', volume=True, mav=(5, 20),
                                             style=korean_style, datetime_format=dt_format,
                                             show_nontrading=False, warn_too_much_data=10000, 
                                             addplot=apds, panel_ratios=panel_ratios,
                                             returnfig=True, figsize=(12, fig_height))

                        ax_main, ax_vol = axes[0], axes[2]
                        if ticker.endswith('.KS') or ticker.endswith('.KQ'):
                            ax_main.yaxis.set_major_formatter(ticker_module.StrMethodFormatter('{x:,.0f}'))
                        else:
                            ax_main.yaxis.set_major_formatter(ticker_module.StrMethodFormatter('{x:,.2f}'))
                        ax_vol.yaxis.set_major_formatter(ticker_module.StrMethodFormatter('{x:,.0f}'))

                        display_title = f"{search_input} ({ticker}) 주가 흐름" if search_input != ticker else f"{ticker} 주가 흐름"
                        ax_main.set_title(display_title, fontweight='bold', fontsize=16, pad=15)

                        st.pyplot(fig)
                        
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")

# ==========================================
# 3. 아이 일정 메뉴 (Child's Schedule)
# ==========================================
elif menu == "👧 아이 일정":
    st.title("👧 온유 일정 관리")
    
    tab1, tab2 = st.tabs(["🏫 1. 학교 일정 (등하교 체크)", "🎒 2. 학원 일정 (스케쥴표)"])
    
    # --- 하위 메뉴 1: 학교 일정 ---
    with tab1:
        st.subheader("✅ 오늘 학교에 잘 다녀왔나요?")
        st.markdown("달력에서 날짜를 선택하고 출석 체크를 해주세요.")
        
        col_date, col_btn = st.columns([1, 1])
        with col_date:
            check_date = st.date_input("날짜 선택", datetime.date.today())
        with col_btn:
            st.write("") 
            st.write("")
            if st.button("🏫 등교 완료! (체크하기)", use_container_width=True):
                date_str = check_date.strftime("%Y-%m-%d")
                if date_str not in st.session_state.attendance:
                    st.session_state.attendance.add(date_str)
                    st.success(f"🎉 {date_str} - 등교 기록이 성공적으로 저장되었습니다!")
                    st.balloons() 
                else:
                    st.warning("이미 체크가 완료된 날짜입니다.")
        
        st.markdown("---")
        st.subheader("🗓️ 등교 완료 기록")
        if st.session_state.attendance:
            sorted_dates = sorted(list(st.session_state.attendance), reverse=True)
            df_attendance = pd.DataFrame({"✅ 학교 간 날짜": sorted_dates})
            df_attendance.index = range(1, len(df_attendance) + 1) 
            st.dataframe(df_attendance, use_container_width=True)
        else:
            st.info("아직 체크된 등교 기록이 없습니다.")

    # --- 하위 메뉴 2: 학원 일정 (수정 기능 추가) ---
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
                    st.session_state.academies.append({
                        "학원명": aca_name,
                        "요일": ", ".join(aca_days),
                        "시간": aca_time.strftime("%H:%M")
                    })
                    st.success(f"{aca_name} 일정이 추가되었습니다!")
                else:
                    st.error("학원 이름과 요일을 모두 입력해 주세요.")
                    
        st.markdown("---")
        
        # --- [수정된 부분] 엑셀처럼 직접 편집 가능한 표 (data_editor) 적용 ---
        st.subheader("📊 온유의 주간 학원 시간표 (직접 수정 가능)")
        st.info("💡 **수정 방법:** 표 안의 글자를 **더블 클릭**하면 내용을 바로 바꿀 수 있습니다.\n\n💡 **삭제 방법:** 삭제하고 싶은 행(줄)의 제일 왼쪽 번호 부분을 클릭해서 선택한 뒤, 키보드의 `Delete` 키를 누르면 지워집니다.")
        
        # 데이터가 없을 때도 표의 틀(컬럼)을 보여주기 위해 처리
        if st.session_state.academies:
            df_academies = pd.DataFrame(st.session_state.academies)
        else:
            df_academies = pd.DataFrame(columns=["학원명", "요일", "시간"])
            
        # 엑셀처럼 편집 가능한 표 띄우기 (num_rows="dynamic" 옵션이 삭제/추가를 가능하게 함)
        edited_df = st.data_editor(df_academies, num_rows="dynamic", use_container_width=True)
        
        # 사용자가 수정한 표의 내용을 실시간으로 다시 저장하여 동기화
        st.session_state.academies = edited_df.to_dict('records')
