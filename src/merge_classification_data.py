import pandas as pd
import numpy as np
import requests
import json
import utils
import argparse

def load_panoptes_data(infile,project_df):
    utils.log('loading file: {0}'.format(infile))
    # read csv file of panoptes classifications
    panoptes_classification_df = pd.read_csv(infile, dtype={'user_id': object})
    # convert 'created_at' to datetime object
    panoptes_classification_df['created_at'] = pd.to_datetime(panoptes_classification_df['created_at'])
    # mark all classifications from the panoptes dump
    panoptes_classification_df['panoptes_dump'] = 1
    # mark all classifications in the panoptes API = 1
    panoptes_classification_df.loc[panoptes_classification_df['project_id'].isin(project_df.loc[project_df['panoptes_api'] == 1]['panoptes_project_id']), 'panoptes_api'] = 1
    panoptes_classification_df.loc[~panoptes_classification_df['project_id'].isin(project_df.loc[project_df['panoptes_api'] == 1]['panoptes_project_id']), 'panoptes_api'] = 0
    # drop all non-overlaping columns
    panoptes_classification_df = panoptes_classification_df[['id', 'project_id', 'user_id', 'created_at', 'panoptes_dump', 'panoptes_api']]
    # rename columns for consistancy
    panoptes_classification_df = panoptes_classification_df.rename(columns={'id': 'classification_id', 'project_id': 'panoptes_project_id'})
    return panoptes_classification_df

def load_ouroboros_data(infile,project_df):
    utils.log('loading file: {0}'.format(infile))
    # read csv file of ouroboros classifications
    ouroboros_classification_df = pd.read_csv(infile)
    # convert 'created_at' to datetime object
    ouroboros_classification_df['created_at'] = pd.to_datetime(ouroboros_classification_df['created_at'])
    # mark all classifications in the ouroboros dump
    ouroboros_classification_df['ouroboros_dump'] = 1
    # rename columns for merging later
    ouroboros_classification_df = ouroboros_classification_df.rename(columns={'project_id':'ouroboros_mongo_id',
                                                                              '_id':'classification_id',
                                                                              'user_name':'user_id'})
    # merge panoptes project id field with classification df
    ouroboros_classification_df = ouroboros_classification_df.merge(project_df[['ouroboros_mongo_id', 'panoptes_project_id', 'panoptes_project_name']], on='ouroboros_mongo_id')
    # mark projects that are in the panoptes api = 1
    ouroboros_classification_df.loc[ouroboros_classification_df['panoptes_project_id'].isin(project_df.loc[project_df['panoptes_api'] == 1]['panoptes_project_id']), 'panoptes_api'] = 1
    ouroboros_classification_df.loc[~ouroboros_classification_df['panoptes_project_id'].isin(project_df.loc[project_df['panoptes_api'] == 1]['panoptes_project_id']), 'panoptes_api'] = 0
    # drop all non-overlapping columns
    ouroboros_classification_df = ouroboros_classification_df[['classification_id', 'created_at', 'user_id', 'tutorial', 'panoptes_project_id', 'ouroboros_dump', 'panoptes_api']]
    return ouroboros_classification_df

def merge_and_format(panoptes_classification_df,ouroboros_classification_df):
    utils.log('appending dfs')
    # merge classification dfs
    result_df = ouroboros_classification_df.append(panoptes_classification_df)
    # change null fields to 0
    result_df.loc[result_df['panoptes_dump'].isnull(), 'panoptes_dump'] = 0
    result_df.loc[result_df['ouroboros_dump'].isnull(), 'ouroboros_dump'] = 0
    return result_df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='import a directory of bson dumps to mongo')
    parser.add_argument('-o','--outfile',
                        help='output directory path')
    parser.add_argument('--ouroboros',
                        help='a csv of ouroboros projects created from a mongo dump')
    parser.add_argument('--panoptes',
                        help='a csv of panoptes classifications')
    parser.add_argument('--project',
                        help='a csv of projects from both ouroboros and panoptes')
    args = parser.parse_args()
    # load project table
    project_df = pd.read_csv(args.project)
    panoptes_classification_df = load_panoptes_data(infile=args.panoptes,
                                                    project_df=project_df)
    ouroboros_classification_df = load_ouroboros_data(infile=args.ouroboros,
                                                      project_df=project_df)
    result_df = merge_and_format(panoptes_classification_df=panoptes_classification_df,
                                 ouroboros_classification_df=ouroboros_classification_df)
    utils.log('writing file: {0}'.format(args.outfile))
    result_df.to_csv(args.outfile,index=False)
