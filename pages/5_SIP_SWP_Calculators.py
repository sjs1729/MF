import streamlit as st
import numpy as np
import pandas as pd
import datetime as dt
import time
from scipy import optimize
import math
import plotly.express as px
from urllib.request import urlopen
import json
from shared_functions import *


st.set_page_config(
    page_title="GroWealth Investments       ",
    page_icon="nirvana.ico",
    layout="wide",
)


np.set_printoptions(precision=3)

tday = dt.datetime.today()

#col1, col2 = st.sidebar.columns(2)
#col1.image('gw_logo.png', width=300)

@st.cache_data()
def get_mf_perf():
    df = pd.read_csv('mf_data.csv')
    df['Date'] = df['Date'].apply(lambda x: dt.datetime.strptime(x,'%Y-%m-%d'))

    df.set_index('Date',inplace=True)

    df_perf = pd.read_csv('revised_mf_perf.csv')
    df_perf.set_index('Scheme_Code', inplace=True)

    df_port_dtl = pd.read_csv('mf_port_detail.csv')

    return df, df_perf, df_port_dtl

@st.cache_data()
def get_historical_nav(amfi_code,tday):
    try:
        success = 'N'
        url = 'https://api.mfapi.in/mf/{}'.format(amfi_code)
        response = urlopen(url)
        result = json.loads(response.read())
        data = result['data']
        nav_list = []
        for rec in reversed(data):
            dt_rec = dt.datetime.strptime(rec['date'], '%d-%m-%Y').date()
            nav = float(rec['nav'])
            values = dt_rec, nav
            nav_list.append(values)

        df_mf = pd.DataFrame(nav_list,columns=['Date','Nav'])
        df_mf.set_index('Date',inplace=True)

    except:
        result='{}'.format(success)
        return result

    return df_mf

def xirr(rate,cash_flow,terminal_value=0):

    npv = 0
    for i in cash_flow.index:
        nYears = cash_flow.loc[i,'Num_Days']/365
        pv = cash_flow.loc[i,'Tran_Value']*(pow((1 + rate / 100), nYears))
        npv = npv + pv

    return  npv+terminal_value

html_text = '<p style="text-align:center">'
html_text = html_text + '<strong><span style="font-family: Verdana, Geneva, sans-serif; font-size: 30px;">'
html_text = html_text + '<span style="color: rgb(9, 0, 220);text-align:center;">Systematic Investment Calculators</span></strong>'

st.markdown(html_text,unsafe_allow_html=True)

df, df_mf_perf, df_port_dtl = get_mf_perf()

sip, swp = st.tabs(["SIP - Calculator", "SWP - Calculator"])

with sip:
    col1,col,col2 = st.columns((6,1,7))

   #st.image("https://static.streamlit.io/examples/cat.jpg", width=200)
    mthly_sip = col1.number_input("Monthly SIP", min_value=0, step=1000, value=1000)
    investment_period = col1.number_input("Investment period (in years)", min_value=1, max_value=50, value=10)
    step_up_pct = col1.number_input("Annual % Increment in Monthly SIP", min_value=0.0, max_value=50.0, value=0.0, step=0.5)

    expected_return = col1.number_input("Expected return (%)", min_value=0.0, max_value=20.0, step=0.5, value=8.0)

    # Calculations
    monthly_sip = mthly_sip
    investment_value = 0
    total_investment = 0
    rec = []
    for i in range(investment_period * 12):
        if i !=0 and i%12 == 0:
            monthly_sip  = monthly_sip * (1 + step_up_pct/100.0)
        investment_value += monthly_sip
        total_investment += monthly_sip
        investment_value *= (1 + expected_return / 100 / 12)


        values = i+1, monthly_sip,investment_value
        rec.append(values)


    sip_df = pd.DataFrame(rec,columns=['Month','SIP','Fund Value'])
    sip_df.set_index('Month', inplace=True)

    html_text = '<p style="text-align:center">'
    html_text = html_text + '<strong><span style="font-family: Verdana, Geneva, sans-serif; font-size: 11px;">'
    html_text = html_text + '<span style="color: rgb(65, 168, 95);text-align:center;">Investment Value:</span></strong>'
    html_text = html_text + '<span style="color: rgb(0,0, 200);"> {}</span>'.format(display_amount(investment_value))
    html_text = html_text + '<BR><strong><span style="font-family: Verdana, Geneva, sans-serif; font-size: 11px;">'
    html_text = html_text + '<span style="color: rgb(65, 168, 95);text-align:center;">Amount Invested:</span></strong>'
    html_text = html_text + '<span style="color: rgb(0,0, 200);"> {}</span><span>  | </span>'.format(display_amount(total_investment))
    html_text = html_text + '<strong><span style="font-family: Verdana, Geneva, sans-serif; font-size: 11px;">'
    html_text = html_text + '<span style="color: rgb(65, 168, 95);text-align:center;">Interest Earned:</span></strong>'
    html_text = html_text + '<span style="color: rgb(0,0, 200);"> {}  </span>'.format(display_amount(investment_value - total_investment))
    html_text = html_text + '<BR></p>'
    col2.markdown(html_text,unsafe_allow_html=True)

    config = {'displayModeBar': False}

    fig = px.line(sip_df[['Fund Value']])


    fig.update_layout(title_text="Fund Growth - Fixed Return",
                              title_x=0.35,
                              title_font_size=16,
                              xaxis_title="Months",
                              yaxis_title="Fund Value")

    fig.update_layout(margin=dict(l=1,r=1,b=1,t=30))

    fig.update_layout(showlegend=False)
    fig.update_layout(legend_title='')
    fig.update_layout(legend=dict(
                        x=0.3,
                        y=-0.25,
                        traceorder='normal',
                        font=dict(size=12,)
                     ))

    fig.update_layout(height=300)
    fig.update_layout(width=450)

    #col2.markdown('<BR>',unsafe_allow_html=True)
    col2.plotly_chart(fig,config=config)
    #col2.markdown(html_text,unsafe_allow_html=True)

    col1.markdown('<BR><BR>',unsafe_allow_html=True)
    checked = col1.checkbox("Back Test with MF Market Data")

    if checked:
        st_date = col1.date_input("Start Date", dt.date(2018, 1, 1))
        st_date = dt.datetime(st_date.year, st_date.month, st_date.day)
        st_date = st_date - dt.timedelta(days=1)
        #start_date = start_date.date()

        end_date = col1.date_input("End Date", dt.date.today(), min_value=st_date)
        end_date = dt.datetime(end_date.year, end_date.month, end_date.day)
        end_date = end_date + dt.timedelta(days=1)

        df_mf_perf['Inception_Date']= pd.to_datetime(df_mf_perf['Inception_Date'])

        df_mf_perf_sel = df_mf_perf[df_mf_perf['Inception_Date'] < st_date]
        schm_list = [ "{}-{}".format(j, df_mf_perf_sel.loc[j]['Scheme_Name']) for j in df_mf_perf_sel.index ]



        schm_select = col1.selectbox("Select Scheme",schm_list,0)
        amfi_code = int(schm_select.split("-")[0])
        schm_select = schm_select.split("-")[1]

        df_mf = get_historical_nav(amfi_code,tday.day)
        #col1.write(type(df_mf.index[0]))
        df_mf = df_mf[(df_mf.index > st_date.date()) & (df_mf.index < end_date.date())]
        df_mf['Units'] = 0.0
        df_mf['Tran_Value'] = 0.0
        df_mf['Num_Days'] = 0.0

        i = 0
        nTran = 0
        units = 0.0
        monthly_sip = mthly_sip
        for j in df_mf.index:


            if i%21 == 0:
                if nTran != 0 and nTran % 12 == 0:
                    monthly_sip  = monthly_sip * (1 + step_up_pct/100.0)
                    #col1.write("{} - {}".format(nTran,display_amount(monthly_sip)))

                nTran = nTran + 1
                #col1.write("{} - {}".format(nTran,i))

                nav = df_mf.loc[j]['Nav']
                units = units + monthly_sip/nav
                df_mf.at[j,'Tran_Value'] = monthly_sip
                df_mf.at[j,'Num_Days'] = (tday.date() - j).days

            i = i + 1
            df_mf.at[j,'Units'] = units

        df_mf['Fund Value'] = df_mf['Nav'] * df_mf['Units']

        #col1.write("Total Investment - {} | Value - {}".format(display_amount(df_mf['Tran_Value'].sum()),display_amount(df_mf['Fund Value'].iloc[-1])))
        #df_mf = df_mf[schm_select]
        #col1.write(df_mf)
        #df_mf.to_csv('SIP.csv')
        df_cash_flow = df_mf[df_mf['Tran_Value'] != 0][['Tran_Value','Num_Days']]
        mkt_amt_invested = df_mf['Tran_Value'].sum()
        mkt_value = df_mf['Fund Value'].iloc[-1]
        mkt_gains = mkt_value - mkt_amt_invested
        market_xirr = round(optimize.newton(xirr, 3, args=(df_cash_flow, mkt_value * -1.0,)),2)
        #col1.write(market_xirr)

        html_text = '<p style="text-align:center">'
        html_text = html_text + '<strong><span style="font-family: Verdana, Geneva, sans-serif; font-size: 11px;">'
        html_text = html_text + '<span style="color: rgb(65, 168, 95);text-align:center;">Investment Value:</span></strong>'
        html_text = html_text + '<span style="color: rgb(0,0, 200);"> {}</span>'.format(display_amount(mkt_value))
        html_text = html_text + '<BR><strong><span style="font-family: Verdana, Geneva, sans-serif; font-size: 11px;">'
        html_text = html_text + '<span style="color: rgb(65, 168, 95);text-align:center;">Amt Invested:</span></strong>'
        html_text = html_text + '<span style="color: rgb(0,0, 200);"> {}</span><span>  | </span>'.format(display_amount(mkt_amt_invested))
        html_text = html_text + '<strong><span style="font-family: Verdana, Geneva, sans-serif; font-size: 11px;">'
        html_text = html_text + '<span style="color: rgb(65, 168, 95);text-align:center;">Total Gain:</span></strong>'
        html_text = html_text + '<span style="color: rgb(0,0, 200);"> {}  </span><span>  | </span>'.format(display_amount(mkt_gains))
        html_text = html_text + '<strong><span style="font-family: Verdana, Geneva, sans-serif; font-size: 11px;">'
        html_text = html_text + '<span style="color: rgb(65, 168, 95);text-align:center;">XIRR:</span></strong>'
        html_text = html_text + '<span style="color: rgb(0,0, 200);"> {}%  </span>'.format(market_xirr)
        html_text = html_text + '<BR></p>'
        col2.markdown(html_text,unsafe_allow_html=True)

        fig1 = px.line(df_mf[['Fund Value']])


        fig1.update_layout(title_text="Fund - Market Return",
                                  title_x=0.35,
                                  title_font_size=16,
                                  xaxis_title="",
                                  yaxis_title="Fund Value")

        fig1.update_layout(margin=dict(l=1,r=1,b=1,t=30))

        fig1.update_layout(showlegend=False)
        fig1.update_layout(legend_title='')
        fig1.update_layout(legend=dict(
                            x=0.3,
                            y=-0.25,
                            traceorder='normal',
                            font=dict(size=12,)
                         ))

        fig1.update_layout(height=300)
        fig1.update_layout(width=450)

        #col2.markdown('<BR>',unsafe_allow_html=True)
        col2.plotly_chart(fig1,config=config)
        #col2.markdown(html_text,unsafe_allow_html=True)


        #col1.write(df_cash_flow)



with swp:

    html_text = '<p style="text-align:center">'
    html_text = html_text + '<strong><span style="font-family: Verdana, Geneva, sans-serif; font-size: 24px;">'
    html_text = html_text + '<span style="color: rgb(65, 168, 95);text-align:center;">SWP Calculator Coming Soon:</span></strong>'

    st.markdown(html_text,unsafe_allow_html=True)