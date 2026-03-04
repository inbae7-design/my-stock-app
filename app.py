import streamlit as st
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import FinanceDataReader as fdr
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker_module
import platform

st.set_page_config(page_title="프로급 실시간 주식 차트", layout="wide")

if platform.system() == 'Windows':
    plt.rcParams['font.family'] = 'Malgun Gothic'
elif platform.system() == 'Darwin':
    plt.rcParams['font.family'] = 'AppleGothic'
else:
    plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False

if 'history' not in st.session_state:
    st.session_state.history = []
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""

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

# --- 사이드바: 설정 및 검색 기록 ---
st.sidebar.title("⚙️ 차트 설정")
show_macd = st.sidebar.checkbox("MACD 보조지표 켜기", value=False)
show_rsi = st.sidebar.checkbox("RSI 보조지표 켜기", value=False)

st.sidebar.markdown("---")
st.sidebar.title("🕒 최근 검색 기록")
for item in st.session_state.history:
    if st.sidebar.button(item, key=f"btn_{item}"):
        st.session_state.search_query = item

# --- 메인 화면 ---
st.title("📈 프로급 실시간 주식 차트 웹 서비스")

col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    search_input = st.text_input("회사명 또는 종목코드 (예: 삼성전자, AAPL)", value=st.session_state.search_query)
with col2:
    interval = st.selectbox("시간 간격", ["1m", "1h", "1d", "1wk", "1mo"], index=2)
with col3:
    st.write("") 
    st.write("")
    search_btn = st.button("차트 그리기", use_container_width=True)

# --- 차트 그리기 ---
if search_btn or search_input:
    if search_input:
        if search_input in st.session_state.history:
            st.session_state.history.remove(search_input)
        st.session_state.history.insert(0, search_input)
        st.session_state.history = st.session_state.history[:10]

        krx_df = load_krx_data()
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

                    # 1. 보조지표 계산 로직 추가
                    # RSI 계산 (14일 기준)
                    delta = df['Close'].diff()
                    up = delta.clip(lower=0)
                    down = -1 * delta.clip(upper=0)
                    ema_up = up.ewm(com=13, adjust=False).mean()
                    ema_down = down.ewm(com=13, adjust=False).mean()
                    rs = ema_up / ema_down
                    df['RSI'] = 100 - (100 / (1 + rs))

                    # MACD 계산 (12일, 26일, 9일 기준)
                    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
                    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
                    df['MACD'] = exp1 - exp2
                    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
                    df['MACD_Hist'] = df['MACD'] - df['Signal']

                    # 2. 체크박스 상태에 따라 차트에 추가할 패널(층) 구성
                    apds = []
                    panel_ratios = [3, 1] # 기본 [캔들차트 3 : 거래량 1] 비율
                    current_panel = 2     # MACD, RSI가 들어갈 층수

                    if show_macd:
                        apds.append(mpf.make_addplot(df['MACD'], panel=current_panel, color='fuchsia', secondary_y=False))
                        apds.append(mpf.make_addplot(df['Signal'], panel=current_panel, color='b', secondary_y=False))
                        apds.append(mpf.make_addplot(df['MACD_Hist'], type='bar', panel=current_panel, color='dimgray', secondary_y=False))
                        panel_ratios.append(1) # MACD 패널 비율 1 추가
                        current_panel += 1

                    if show_rsi:
                        apds.append(mpf.make_addplot(df['RSI'], panel=current_panel, color='purple', ylabel='RSI', secondary_y=False))
                        # RSI 과매수(70)/과매도(30) 기준선 추가
                        apds.append(mpf.make_addplot([70]*len(df), panel=current_panel, color='r', linestyle='dashed', secondary_y=False))
                        apds.append(mpf.make_addplot([30]*len(df), panel=current_panel, color='b', linestyle='dashed', secondary_y=False))
                        panel_ratios.append(1) # RSI 패널 비율 1 추가
                        current_panel += 1

                    dt_format = '%y-%m-%d %H:%M' if interval in ['1m', '1h'] else '%Y-%m-%d'
                    mc = mpf.make_marketcolors(up='red', down='blue', edge='inherit', wick='inherit', volume='inherit')
                    korean_style = mpf.make_mpf_style(marketcolors=mc, gridstyle='--')

                    # 3. addplot과 동적 패널 비율(panel_ratios)을 적용하여 차트 그리기
                    # 지표가 늘어날 때마다 차트의 세로 길이(figsize)도 동적으로 늘려줍니다.
                    fig_height = 7 + (current_panel - 2) * 2.5
                    fig, axes = mpf.plot(df, type='candle', volume=True, mav=(5, 20),
                                         style=korean_style, datetime_format=dt_format,
                                         show_nontrading=False, warn_too_much_data=10000, 
                                         addplot=apds, panel_ratios=panel_ratios,
                                         returnfig=True, figsize=(12, fig_height))

                    # 가격 및 거래량 축 콤마 포맷팅
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
