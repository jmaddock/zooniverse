import argparse
import pandas as pd
import numpy as np
import requests
import json
import utils

# set the API endpoint
BASE_URL = r'https://panoptes.zooniverse.org/api/projects'

def create_panoptes_project_df_from_dump(infile_name):
    utils.log('reading file: {0}'.format(infile_name))
    # read csv file of panoptes classifications
    classification_df = pd.read_csv(infile_name)
    # create a project dataframe that contains the total number of classifications per project
    project_df = classification_df.groupby('project_id').size().to_frame('panoptes_dump_classification_count')
    # get the workflow IDs for each project and store as a list
    project_df = project_df.merge(classification_df.groupby('project_id')['workflow_id'].unique().to_frame('panoptes_dump_workflows'),left_index=True,right_index=True)
    # reset index
    project_df = project_df.reset_index()
    # create 'panoptes_dump' column
    project_df['panoptes_dump'] = 1
    # rename project_id field for merge later
    project_df = project_df.rename(columns={'project_id':'panoptes_project_id'})
    utils.log('processed file: {0}'.format(infile_name))
    return project_df

def get_panoptes_API_results(base_url):
    # set necessary headers for zooniverse API
    headers = {
        'Accept':'application/vnd.api+json; version=1',
        'Content-Type':'application/json'
    }
    params = {}
    api_result_df = pd.DataFrame()
    while True:
        # send and recieve HTTP request to API endpoint
        r = requests.get(base_url,
                        params=params,
                        headers=headers)
        utils.log('querying API: {0}'.format(r.url))
        # convert the result to JSON
        api_result = r.json()

        # iterate through each project in a page of API results
        for project in api_result['projects']:
            # collect relivant fields from json
            api_result_dict = {
                'panoptes_project_id':project['id'],
                'panoptes_project_name':project['display_name'],
                'panoptes_migrated':project['migrated'],
                'panoptes_description':project['description'],
                'panoptes_live':project['live'],
                'panoptes_launch_date':project['launch_date'],
                'panoptes_completeness':project['completeness'],
                'panoptes_api_subject_count':project['subjects_count'],
                'panoptes_api_classificaitons_count':project['classifiers_count'],
            }
            # collect the workflow information if it exists
            # this is useful for comparing dump results against API results
            if 'workflows' in project['links']:
                api_result_dict['panoptes_api_workflows'] = project['links']['workflows']
            else:
                api_result_dict['panoptes_api_workflows'] = None
            # collect the project roles if they're listed
            if 'project_roles' in project['links']:
                api_result_dict['panoptes_api_roles'] = project['links']['project_roles']
            else:
                api_result_dict['panoptes_api_roles'] = None
            # add the project data to the projects dataframe
            api_result_df = api_result_df.append(pd.DataFrame([api_result_dict]))

        # if there is another page of search results, add that href to the next query
        # else return the API result
        if api_result['meta']['projects']['next_href']:
            params['page'] = api_result['meta']['projects']['next_href'].split('=')[-1]
        else:
            break

    # convert the project ID from a string to a numeric field
    api_result_df['panoptes_project_id'] = pd.to_numeric(api_result_df['panoptes_project_id'])
    # create a panoptes_api field
    api_result_df['panoptes_api'] = 1
    return api_result_df

def create_ouroboros_project_df_from_dump(infile_name):
    utils.log('reading file: {0}'.format(infile_name))
    # read csv file of panoptes classifications
    ouroboros_project_df = pd.read_csv(infile_name)
    # rename files for consistency
    ouroboros_project_df = ouroboros_project_df.rename(columns={'_id':'ouroboros_mongo_id',
                                                                'panoptes_id':'panoptes_project_id',
                                                                'activated_subjects_at':'ouroboros_meta_activated_subjects_at',
                                                                'classification_count':'ouroboros_meta_classification_count',
                                                                'complete_count':'ouroboros_meta_complete_count',
                                                                'created_at':'ouroboros_meta_created_at',
                                                                'display_name':'ouroboros_project_name',
                                                                'panoptes_id':'panoptes_project_id',
                                                                'user_count':'ouroboros_meta_user_count'})
    # create a ouroboros_dump field
    ouroboros_project_df['ouroboros_dump'] = 1
    # drop un-needed fields
    ouroboros_project_df = ouroboros_project_df[['ouroboros_mongo_id',
                                                 'ouroboros_meta_activated_subjects_at',
                                                 'ouroboros_meta_classification_count',
                                                 'ouroboros_meta_complete_count',
                                                 'ouroboros_meta_created_at',
                                                 'ouroboros_project_name',
                                                 'panoptes_project_id', 
                                                 'ouroboros_meta_user_count',
                                                 'ouroboros_dump']]
    return ouroboros_project_df

def merge_all_projects(panoptes_dump,panoptes_api,ouroboros_dump):
    utils.log('merging dataframes')
    # join all 3 dataframes
    joined_df = panoptes_api.merge(panoptes_dump,on='panoptes_project_id',how='outer')
    joined_df = joined_df.merge(ouroboros_dump,on='panoptes_project_id',how='outer')
    # set NaN values to 0
    joined_df.loc[joined_df['panoptes_dump'].isnull(),'panoptes_dump'] = 0
    joined_df.loc[joined_df['panoptes_api'].isnull(),'panoptes_api'] = 0
    joined_df.loc[joined_df['ouroboros_dump'].isnull(),'ouroboros_dump'] = 0
    # drop non-uniques base on panoptes_project_id
    joined_df = joined_df.drop_duplicates(subset='panoptes_project_id',keep='first')
    return joined_df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='import a directory of bson dumps to mongo')
    parser.add_argument('-o','--outfile',
                        help='output directory path')
    parser.add_argument('--ouroboros',
                        help='a csv of ouroboros projects created from a mongo dump')
    parser.add_argument('--panoptes',
                        help='a csv of panoptes classifications')
    args = parser.parse_args()
    panoptes_dump = create_panoptes_project_df_from_dump(infile_name=args.panoptes)
    panoptes_api = get_panoptes_API_results(base_url=BASE_URL)
    ouroboros_dump = create_ouroboros_project_df_from_dump(infile_name=args.ouroboros)
    result_df = merge_all_projects(panoptes_dump=panoptes_dump,
                                   panoptes_api=panoptes_api,
                                   ouroboros_dump=ouroboros_dump)
    utils.log('writing file: {0}'.format(args.outfile))
    result_df.to_csv(args.outfile,index=False)
