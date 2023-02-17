# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.14.4
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %%capture
# !pip3 install pandas python-dotenv

# +
import os

import pandas as pd
from pprint import pprint

from dotenv import load_dotenv
load_dotenv()


known_utm_combinations = [
    ["linkedin", "apply_directly_linkedin"],  # Apply for job directy through linkedin
    ["linkedin", "linkedin_profile_page"],
    ["linkedin", "msg_linkedin"], # Find someone in a company that is hiring

    ["email", "msg_email"], # Message someone directly

    ["github", "cv_repository_readme"], #Link placed in readme.md

    ["pdf", "backend-developer-v1"], # Placed in pdf
    ["pdf", "product-manager-v1"]
]

known_utm_combinations_df = pd.DataFrame(known_utm_combinations, columns=['utm_source', 'utm_campaign'])

unique_utm_sources = known_utm_combinations_df['utm_source'].unique()
unique_utm_campaigns = known_utm_combinations_df['utm_campaign'].unique()

# Make analytics for certain period of time
days_ago = 30

mock = eval(os.getenv("MOCK", "False"))

# Timezone
timezone = "Etc/UTC"

# +
import requests
import pytz

from datetime import datetime, timedelta
from random import randrange


fields_stats_for_simple_analytics = [
    "pageviews", # the total amount of page views in the specified period
    "visitors", # the total amount of visitors (unique page views) in the specified period
    "histogram", # an array with page views and visitors per day
    "countries", # a list of country codes
    "utm_sources",
    "utm_campaigns",
    "referrers",
    "seconds_on_page" # the median of seconds a visitor spent on the page
]


def mock_simple_analytics_stats(stats):
    stats = stats.copy()
    stats['pageviews'] = 0
    stats['visitors'] = 0
    
    for histogram in stats['histogram']:
        page_views = randrange(0, 100)
        visitors = page_views // randrange(3, 5)
        
        histogram['pageviews'] = page_views
        histogram['visitors'] = visitors
        
        # Add to overall stats
        stats['pageviews'] += page_views
        stats['visitors'] += visitors
    
    
    stats['seconds_on_page'] = randrange(1, 35)
    
    # It is possible to populate using average amount of visitors, distribute over know utm tags and non-utm visitors
    stats['utm_campaigns'] = list(map(lambda value: {
        'pageviews': randrange(1, 35),
        'seconds_on_page': randrange(1, 30),
        'value': value,
        'visitors': randrange(10, 50),
    }, unique_utm_campaigns))

    stats['utm_sources'] = list(map(lambda value: {
        'pageviews': randrange(1, 35),
        'seconds_on_page': randrange(1, 30),
        'value': value,
        'visitors': randrange(10, 50),
    }, unique_utm_sources))
    
    return stats
    


def convert_and_filter_utm_params(stats_utm, known_utm_values):
    df = pd.DataFrame(stats_utm)
    df = df[df['value'].isin(known_utm_values)]
    return df if not df.empty else None


def fetch_simple_analytics_stats():
    fields_stats_for_simple_analytics_str = ','.join(fields_stats_for_simple_analytics)
    url = f"https://simpleanalytics.com/artbred.io.json?info=false&version=5&fields={fields_stats_for_simple_analytics_str}&timezone={timezone}"
    
    current_date = datetime.now(pytz.timezone(timezone)).date()
    days_before = current_date - timedelta(days=days_ago)
    
    url += f"&start={days_before}&end={current_date}"

    response = requests.get(url, headers={
        "Content-Type": "application/json",
    })
        
    stats = response.json()
    if not stats['ok']:
        raise ValueError(stats)
    
    if mock:
        stats = mock_simple_analytics_stats(stats)

    return stats


def get_simple_analytics_stats():
    stats = fetch_simple_analytics_stats()

    if 'countries' in stats:
        del stats['countries']

    stats['histogram'] = pd.DataFrame(stats['histogram'])
    stats['histogram']['date'] = pd.to_datetime(stats['histogram']['date'])
    stats['histogram'].set_index('date', inplace=True)

    # Delete unknown utm params and convert to pandas data frame
    stats['utm_sources'] = convert_and_filter_utm_params(stats['utm_sources'], unique_utm_sources)
    stats['utm_campaigns'] = convert_and_filter_utm_params(stats['utm_campaigns'], unique_utm_campaigns)

    stats['referrers'] = pd.DataFrame(stats['referrers'])

    return stats


simple_analytics_stats = get_simple_analytics_stats()
pprint(simple_analytics_stats['histogram'])
print('-' * 40)
pprint(simple_analytics_stats['utm_campaigns'])
print('-' * 40)
pprint(simple_analytics_stats['utm_sources'])
# -

# %%capture
# !pip3 install redis

# +
import sys
import time
import json
import string
import pandas as pd
import requests
import random
import numpy as np

sys.path.append('../app')

from storage import create_redis_connection, labels_prefix_key, requests_params_set_prefix_key, decode_redis_data, downloads_by_label_id_set_key


def api_call(query_position, **kwargs):
    params = {k: v for k, v in kwargs.items() if v is not None}
    query_url = '&'.join([f"{k}={v}" for k, v in params.items()])
    response = requests.post("http://127.0.0.1:8000/score?" + query_url, json.dumps({"position": query_position}))
    if response.status_code == 200:
        requests.post("http://127.0.0.1:8000/download?" + query_url, json.dumps({"token": response.json()['token']}))


def fill_redis_with_fake_data():
    # Define probabilities
    positions = {"backend developer": 0.4, "product manager": 0.6}
    real_position_probability = 0.7
    modify_real_position_probability = 0.85
    utm_params_probability = 0.8

    for i in range(100):
        position, utm_campaign, utm_source = '', None, None

        if random.random() < real_position_probability:
            position = random.choices(list(positions.keys()), weights=list(positions.values()))[0]

            if random.random() < modify_real_position_probability:
                num_chars_to_replace = random.randrange(0, len(position) // 4)
                indices_to_replace = random.sample(range(len(position)), num_chars_to_replace)
                random_string = ''.join(random.choices(string.ascii_letters, k=num_chars_to_replace))
                modified_position = "".join([random_string[indices_to_replace.index(i)] if i in indices_to_replace else position[i] for i in range(len(position))])
                position = modified_position
        else:
            position = ''.join(random.choices(string.ascii_letters, k=random.randrange(5, 45)))

        if random.random() < utm_params_probability:
            utm_campaign = random.choice(unique_utm_campaigns)
            if random.random() < 0.9:
                utm_source = random.choice(unique_utm_sources)

        api_call(position, utm_source=utm_source, utm_campaign=utm_campaign)

def get_labels_data_from_redis(conn):
    labels_list = []

    for label_key in conn.keys(labels_prefix_key + "*"):
        label_byte = conn.hgetall(label_key)
        label = decode_redis_data(label_byte)
        labels_list.append(label)

    return pd.DataFrame(labels_list, columns=["id", "position"])

def get_requests_params_from_redis(conn):
    request_params = {}

    time_now = int(time.time())
    start_time = time_now - (days_ago * 24 * 60 * 60)

    for endpoint_request_key_byte in conn.keys(requests_params_set_prefix_key + "*"):
        endpoint_request_key = decode_redis_data(endpoint_request_key_byte)
        endpoint = endpoint_request_key.replace(requests_params_set_prefix_key, "")
        
        params_for_endpoint_byte = conn.zrangebyscore(endpoint_request_key, start_time, time_now)
        params_for_endpoint = decode_redis_data(params_for_endpoint_byte)
        params_for_endpoint_df = pd.DataFrame(params_for_endpoint)

        # Replace unknown utm source / utm campaign with NaN
        params_for_endpoint_df.replace({
            'utm_source': {val: np.nan for val in set(params_for_endpoint_df['utm_source']) - set(unique_utm_sources) - {np.nan}},
            'utm_campaign': {val: np.nan for val in set(params_for_endpoint_df['utm_campaign']) - set(unique_utm_campaigns) - {np.nan}}
        }, inplace=True)

        params_for_endpoint_df.loc[:, "date"] = pd.to_datetime(params_for_endpoint_df['timestamp'], utc=True, unit='s').dt.date
        params_for_endpoint_df.set_index("date", inplace=True)

        request_params[endpoint] = params_for_endpoint_df

    return request_params 
    

def get_downloads_data_from_redis(conn):
    time_now = int(time.time())
    start_time = time_now - (days_ago * 24 * 60 * 60)

    downloads_bytes = conn.zrangebyscore(downloads_by_label_id_set_key, start_time, time_now)
    downloads_list = decode_redis_data(downloads_bytes)
    downloads_df = pd.DataFrame(downloads_list)

    downloads_df["date"] = pd.to_datetime(downloads_df["timestamp"], utc=True, unit='s').dt.date
    downloads_df.set_index("date", inplace=True)

    return downloads_df


def get_data_from_redis():
    with create_redis_connection() as conn:
        labels_df = get_labels_data_from_redis(conn)
        requests_params_endpoints = get_requests_params_from_redis(conn)
        downloads_df = get_downloads_data_from_redis(conn)
        return labels_df, requests_params_endpoints, downloads_df
    
    
if mock:
    fill_redis_with_fake_data()


labels_df, requests_params_endpoints, downloads_df = get_data_from_redis()
pprint(labels_df)
print('-' * 40)
pprint(requests_params_endpoints)
print('-' * 40)
print(downloads_df)

# +
import pickle

file_name = 'analytics_mock' if mock else 'analytics'

with open(f'../data/analytics/{file_name}.pickle', 'wb') as f:
    pickle.dump({
        "simple_analytics": simple_analytics_stats,
        "labels": labels_df,
        "requests_params_endpoints": requests_params_endpoints,
        "downloads": downloads_df
    }, f)
