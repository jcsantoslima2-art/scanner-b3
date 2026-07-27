"""
Dashboard B3 V5.3 — Streamlit
Interface visual para Watchlist Stateful V5.2.
Não emite recomendação de compra/venda.

Instalação:
  pip install streamlit pandas openpyxl plotly

Execução:
  streamlit run dashboard_b3_v53.py -- --workbook watchlist_v52_prioridades_2025-12-30.xlsx --prices dados_b3.csv
"""
import argparse, pandas as pd, numpy as np
import streamlit as st
import plotly.graph_objects as go

parser=argparse.ArgumentParser(add_help=False)
parser.add_argument("--workbook",default="watchlist_v52_prioridades_2025-12-30.xlsx")
parser.add_argument("--prices",default="dados_b3.csv")
args,_=parser.parse_known_args()

st.set_page_config(page_title="Scanner B3",layout="wide")
st.title("Scanner B3 — Monitor de Estruturas")
st.caption("Detecção estrutural e contexto de mercado. Sem recomendação de compra ou venda.")

@st.cache_data
def load():
    watch=pd.read_excel(args.workbook,sheet_name="Watchlist Atual")
    queue=pd.read_excel(args.workbook,sheet_name="Fila de Alertas")
    hist=pd.read_excel(args.workbook,sheet_name="Historico")
    px=pd.read_csv(args.prices,parse_dates=["date"])
    for z in (watch,queue,hist):
        if "date" in z: z["date"]=pd.to_datetime(z["date"])
    return watch,queue,hist,px

watch,queue,hist,px=load()
latest=pd.to_datetime(watch.date).max() if len(watch) else None

# KPIs
c1,c2,c3,c4=st.columns(4)
c1.metric("Estruturas monitoradas",len(watch))
c2.metric("Alertas imediatos",(queue.delivery=="IMEDIATO").sum() if "delivery" in queue else 0)
c3.metric("Compressões avançadas",(watch.state=="COMPRESSAO_AVANCADA").sum())
c4.metric("Próximas da borda",(watch.state=="PROXIMA_DA_BORDA").sum())

st.subheader("Prioridade agora")
if len(queue):
    cols=[c for c in ["ticker","priority","transition","quality","maturity","dist_support","dist_resistance",
                      "breadth200","b200_chg20"] if c in queue.columns]
    q=queue.sort_values("priority_score",ascending=False)[cols].copy()
    st.dataframe(q,use_container_width=True,hide_index=True)

st.subheader("Watchlist")
f1,f2,f3=st.columns(3)
states=["TODOS"]+sorted(watch.state.dropna().astype(str).unique().tolist())
state=f1.selectbox("Estado",states)
contexts=["TODOS"]+sorted(watch.prior_context.dropna().astype(str).unique().tolist())
context=f2.selectbox("Contexto anterior",contexts)
minmat=f3.slider("Maturidade mínima",0,100,60,5)

w=watch.copy()
if state!="TODOS": w=w[w.state==state]
if context!="TODOS": w=w[w.prior_context==context]
w=w[w.maturity>=minmat].sort_values(["maturity","quality"],ascending=False)
show=[c for c in ["ticker","state","direction","prior_context","quality","maturity","duration",
                  "support","resistance","dist_support","dist_resistance","breadth200","b200_chg20"] if c in w]
st.dataframe(w[show],use_container_width=True,hide_index=True)

st.subheader("Ficha da estrutura")
tickers=w.ticker.tolist() if len(w) else watch.ticker.tolist()
ticker=st.selectbox("Ativo",tickers)
r=watch[watch.ticker==ticker].iloc[0]
m1,m2,m3,m4=st.columns(4)
m1.metric("Qualidade",f"{r.quality:.0f}/100")
m2.metric("Maturidade",f"{r.maturity:.0f}/100")
m3.metric("Suporte",f"R$ {r.support:,.2f}".replace(",", "X").replace(".", ",").replace("X","."))
m4.metric("Resistência",f"R$ {r.resistance:,.2f}".replace(",", "X").replace(".", ",").replace("X","."))

z=px[px.ticker==ticker].sort_values("date").tail(180).copy()
if len(z):
    z["ma50"]=z.close.rolling(50).mean()
    z["ma200"]=z.close.rolling(200).mean()
    fig=go.Figure()
    fig.add_trace(go.Candlestick(x=z.date,open=z.open,high=z.high,low=z.low,close=z.close,name=ticker))
    fig.add_trace(go.Scatter(x=z.date,y=z.ma50,name="MM50"))
    fig.add_trace(go.Scatter(x=z.date,y=z.ma200,name="MM200"))
    fig.add_hline(y=float(r.support),line_dash="dash",annotation_text="Suporte")
    fig.add_hline(y=float(r.resistance),line_dash="dash",annotation_text="Resistência")
    fig.update_layout(height=600,xaxis_rangeslider_visible=False)
    st.plotly_chart(fig,use_container_width=True)

st.subheader("Linha do tempo do episódio")
eh=hist[hist.ticker==ticker].sort_values("date").copy()
if len(eh):
    st.dataframe(eh[[c for c in ["date","episode_id","state","transition","quality","maturity",
                                  "support","resistance","breadth200","b200_chg20"] if c in eh]],
                 use_container_width=True,hide_index=True)

st.caption(f"Base atualizada até {latest.date() if latest is not None else '—'}.")
