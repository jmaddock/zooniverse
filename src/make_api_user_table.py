import argparse
import pandas as pd
import numpy as np
import requests
import json
import utils

BASE_URL = r'https://panoptes.zooniverse.org/api/users'

def get_users_from_api(base_url):
    # set necessary headers for zooniverse API
    headers = {
        'Accept':'application/vnd.api+json; version=1',
        'Content-Type':'application/json'
    }
    params = {'page_size':200}
    api_result_df = pd.DataFrame()
    while True:
        # send and recieve HTTP request to API endpoint
        r = requests.get(base_url,
                        params=params,
                        headers=headers)
        print('querying API: {0}'.format(r.url))
        # convert the result to JSON
        api_result = r.json()

        # iterate through each user in a page of API results
        for user in api_result['users']:
            api_result_dict = {
                'created_at':user['created_at'],
                'display_name':user['display_name'],
                'panoptes_user_id':user['id'],
                'zooniverse_id':user['zooniverse_id']
            }
            api_result_df = api_result_df.append(pd.DataFrame([api_result_dict]))

        # if there is another page of search results, add that href to the next query
        # else return the API result
        if api_result['meta']['users']['next_href']:
            params['page'] = api_result['meta']['users']['next_page']
        else:
            break

    # convert the project ID from a string to a numeric field
    api_result_df['panoptes_user_id'] = pd.to_numeric(api_result_df['panoptes_user_id'])
    api_result_df['zooniverse_id'] = pd.to_numeric(api_result_df['zooniverse_id'])
    return api_result_df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='import a directory of bson dumps to mongo')
    parser.add_argument('-o','--outfile',
                        help='output file path')
    args = parser.parse_args()
    df = get_users_from_api(base_url=BASE_URL)
    utils.log('writing file: {0}'.format(args.outfile))
    df.to_csv(args.outfile,index=False)
