import os
import pickle

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from dotenv import load_dotenv
load_dotenv('../.env')

def load_data(is_mock):
    data_file = f'../data/analytics/analytics{"_mock" if is_mock else ""}.pickle'
    with open(data_file, 'rb') as f:
        data = pickle.load(f)
    return data


def display_web_analytics(data):
    histogram_data = data['simple_analytics']['histogram']
    utm_campaigns_data = data['simple_analytics']['utm_campaigns']
    utm_sources_data = data['simple_analytics']['utm_sources']
    referrers_data = data['simple_analytics']['referrers']

    histogram_ct, utm_ct, referrers_ct, calc_ct = st.container(), st.container(), st.container(), st.container()

    min_histogram_date = histogram_data.index.min()
    max_histogram_date = histogram_data.index.max()

    date_range_selected = histogram_ct.date_input(
        'Select date range:', [min_histogram_date, max_histogram_date], 
        min_value=min_histogram_date, max_value=max_histogram_date
    )

    if len(date_range_selected) != 2: 
        return

    date_range = pd.date_range(
        start=date_range_selected[0], end=date_range_selected[1], 
        inclusive='both', freq='1D'
    )

    histogram_data = histogram_data.loc[date_range]

    histogram_ct.header('Histogram of Visitors and Pageviews')
    histogram_ct.plotly_chart(
        px.bar(histogram_data, x=histogram_data.index, y=['visitors', 'pageviews'], barmode='group')
    )

    histogram_ct.header('Visitors and Pageviews over Time')
    histogram_ct.plotly_chart(
        px.line(histogram_data, x=histogram_data.index, y=['visitors', 'pageviews'], line_shape='spline')
    )

    utm_ct.header('UTM Campaigns (not filtered)')
    utm_ct.dataframe(utm_campaigns_data)

    utm_ct.header('UTM Sources (not filtered)')
    utm_ct.dataframe(utm_sources_data)

    referrers_ct.header("Referrers (not filtered)")
    referrers_ct.dataframe(referrers_data)

    total_pageviews = histogram_data['pageviews'].sum()
    total_visitors = histogram_data['visitors'].sum()

    calc_ct.write(f"Total pageviews for the selected interval is: {total_pageviews}")
    calc_ct.write(f"Total visitors for the selected interval is: {total_visitors}")

    average_stats = histogram_data.mean()

    calc_ct.write(f'The average pageviews for the selected interval is: {average_stats["pageviews"]:.2f}')
    calc_ct.write(f'The average visitors for the selected interval is: {average_stats["visitors"]:.2f}')

    visitors_by_weekday = histogram_data.groupby(histogram_data.index.weekday)['visitors'].sum()
    fig = go.Figure(data=[go.Bar(x=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], y=visitors_by_weekday.values)])
    fig.update_layout(title='Visitors by Weekday', xaxis_title='Day of the week', yaxis_title='Visitors')
    st.plotly_chart(fig)


def display_app_analytics(data):
    labels = data['labels']
    downloads = data['downloads']

    min_downloads_date = downloads.index.min()
    max_downloads_date = downloads.index.max()

    date_range_selected = st.date_input(
        'Select date range:', [min_downloads_date, max_downloads_date], 
        min_value=min_downloads_date, max_value=max_downloads_date
    )

    if len(date_range_selected) != 2: 
        return 

    date_range = pd.date_range(
        start=date_range_selected[0], end=date_range_selected[1], 
        inclusive='both', freq='1D'
    )

    downloads = downloads.loc[date_range]

    if downloads.empty:
        st.info("No downloads available for selected period")
        return

    count_downloads_by_label = downloads['label_id'].value_counts()
    count_downloads_by_position = pd.merge(count_downloads_by_label, labels, how='left', left_index=True, right_on='id')
    count_downloads_by_position = count_downloads_by_position.drop(columns=['id'])
    count_downloads_by_position = count_downloads_by_position.rename(columns={'label_id': 'count'})
    count_by_position = count_downloads_by_position.sort_values(by='count', ascending=False)

    st.write("Amount of resume downloads for each position")
    st.dataframe(count_by_position)

    sources_counts = downloads.groupby('utm_source').size().reset_index(name='count')
    sorted_sources_counts = sources_counts.sort_values(by='count', ascending=False)[['utm_source', 'count']]

    st.write("Utm sources for downloaded resumes")
    st.dataframe(sorted_sources_counts)

    campaign_counts = downloads.groupby('utm_campaign').size().reset_index(name='count')
    sorted_campaign_counts = campaign_counts.sort_values(by='count', ascending=False)[['utm_campaign', 'count']]

    st.write("Utm campaigns for downloaded resumes")
    st.dataframe(sorted_campaign_counts)

    histogram_data = data['simple_analytics']['histogram']
    histogram_data = histogram_data.loc[date_range]

    total_visitors_count = histogram_data['visitors'].sum()
    total_downloads_count = count_by_position['count'].sum()

    conv_rate = total_downloads_count / total_visitors_count * 100
    if conv_rate >= 100: # too fake data
        conv_rate = 3.14

    st.metric("Conversion rate (downloads vs visitors)", f"{conv_rate:.2f}%")


def main():
    st.title('artbred.io analytics dashboard')

    is_mock = eval(os.getenv("MOCK", "True"))
    data = load_data(is_mock)

    if is_mock:
        st.sidebar.write("You are now watching fake data, I will update analytics once I gather real one")

    web_analytics_tab, app_analytics_tab = st.tabs(["Web analytics", "App analytics"])

    with web_analytics_tab:
        display_web_analytics(data)
    
    with app_analytics_tab:
        display_app_analytics(data)


main()