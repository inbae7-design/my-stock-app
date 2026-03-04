import streamlit as st
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import FinanceDataReader as fdr
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker_module
import platform

# --- 1. 웹 페이지 기본 설정 ---
st.set_page_config(page_title="실시간 주식 차트 검색기", layout="wide")

# --- 2. 한글 폰트 및 마이너스 깨짐 방지 ---
if platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
elif platform.system() == 'Darwin':
    plt.rcParams['font.family'] = 'AppleGothic'
else:
    plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False

# --- 3. 세션 상태(Session State) 초기화 ---
# 웹은 새로고침될 때마다 코드가 처음부터 실행되므로, 검색 기록을 세션에 저장하여 유지합니다.
if 'history' not in st.session_state:
    st.session_state.history = []
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""

# --- 4. 한국 주식 DB 불러오기 (캐싱 적용) ---
# @st.cache_data를 붙이면 매번 다운받지 않고 메모리에 저장해두어 속도가 매우 빠릅니다.
@st.cache_data
def load_krx_data():
    return fdr.StockListing('KRX')

def get_ticker_from_name(name, krx_df):
    if name.encode().isalpha():
        return name.upper()
    match = krx_df[krx_df['Name'] == name]
    if not match.empty:
        code = match.iloc[0]['Code']
        market = match.iloc[0]['Market']
        return f"{code}.KS" if 'KOSPI' in market else f"{code}.KQ"
    return name

# --- 5. 좌측 사이드바: 최근 검색 기록 ---
st.sidebar.title("최근 검색 기록")
for item in st.session_state.history:
    # 검색 기록 버튼을 누르면 검색창 입력값을 해당 종목으로 바꿉니다.
    if st.sidebar.button(item, key=f"btn_{item}"):
        st.session_state.search_query = item

# --- 6. 메인 화면 UI ---
st.title("📈 프로급 실시간 주식 차트 웹 서비스")

# 화면을 3개의 열(Column)로 나누어 검색창, 드롭다운, 버튼 배치
col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    search_input = st.text_input("회사명 또는 종목코드 (예: 삼성전자, AAPL)", 
                                 value=st.session_state.search_query)
with col2:
    interval = st.selectbox("시간 간격", ["1m", "1h", "1d", "1wk", "1mo"], index=2)
with col3:
    # 간격 맞춤을 위해 빈 줄 추가
    st.write("") 
    st.write("")
    search_btn = st.button("차트 그리기", use_container_width=True)

# --- 7. 차트 그리기 로직 ---
if search_btn or search_input:
    if search_input:
        # 검색 기록 업데이트
        if search_input in st.session_state.history:
            st.session_state.history.remove(search_input)
        st.session_state.history.insert(0, search_input)
        st.session_state.history = st.session_state.history[:10]

        krx_df = load_krx_data()
        ticker = get_ticker_from_name(search_input, krx_df)
        
        period_map = {'1m': '7d', '1h': '730d', '1d': '5y', '1wk': '5y', '1mo': '10y'}
        period = period_map.get(interval, '1y')

        # 로딩 스피너 애니메이션
        with st.spinner('데이터를 분석하고 차트를 그리는 중입니다...'):
            try:
                df = yf.download(ticker, period=period, interval=interval)
                
                if df.empty:
                    st.error("데이터를 찾을 수 없습니다. 회사명이나 종목 코드를 확인해 주세요.")
                else:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.droplevel(1)

                    dt_format = '%y-%m-%d %H:%M' if interval in ['1m', '1h'] else '%Y-%m-%d'

                    mc = mpf.make_marketcolors(up='red', down='blue', 
                                               edge='inherit', wick='inherit', volume='inherit')
                    korean_style = mpf.make_mpf_style(marketcolors=mc, gridstyle='--')

                    # returnfig=True 옵션을 주어 웹에 띄울 수 있는 피규어(도화지) 객체를 반환받습니다.
                    fig, axes = mpf.plot(df, type='candle', volume=True, mav=(5, 20),
                                         style=korean_style, datetime_format=dt_format,
                                         show_nontrading=False, warn_too_much_data=10000, 
                                         returnfig=True, figsize=(12, 7))

                    # 가격 축(axes[0])과 거래량 축(axes[2]) 콤마 포맷팅
                    ax_main, ax_vol = axes[0], axes[2]
                    
                    if ticker.endswith('.KS') or ticker.endswith('.KQ'):
                        ax_main.yaxis.set_major_formatter(ticker_module.StrMethodFormatter('{x:,.0f}'))
                    else:
                        ax_main.yaxis.set_major_formatter(ticker_module.StrMethodFormatter('{x:,.2f}'))
                    ax_vol.yaxis.set_major_formatter(ticker_module.StrMethodFormatter('{x:,.0f}'))

                    display_title = f"{search_input} ({ticker}) 주가 흐름" if search_input != ticker else f"{ticker} 주가 흐름"
                    ax_main.set_title(display_title, fontweight='bold', fontsize=16, pad=15)

                    # 완성된 차트를 Streamlit 웹 화면에 출력
                    st.pyplot(fig)
                    
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")