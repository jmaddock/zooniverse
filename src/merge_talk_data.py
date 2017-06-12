import pandas as pd
import numpy as np
import json
import argparse
import utils
from ast import literal_eval

def format_panoptes_talk(infile):
    # read csv file of panoptes talk data
    utils.log('loading file: {0}'.format(infile))
    panoptes_comments = pd.read_csv(infile)
    # rename columns for consistancy w/ ouroboros
    panoptes_comments = panoptes_comments.rename(columns={'id':'comment_id',
                                                          'focus_type':'focus_base_type',
                                                          'user_login':'user_name',
                                                          'mentioning':'mentions',
                                                          'tagging':'tags',
                                                          'reply_id':'response_to_id',
                                                          'project_id':'panoptes_project_id'})
    # indicate that this conversation came from the panoptes dump
    panoptes_comments['panoptes_dump'] = 1
    # specify fields to keep in final df
    panoptes_comments = panoptes_comments[['comment_id',
                                           'body',
                                           'focus_id',
                                           'focus_base_type',
                                           'discussion_id',
                                           'user_id',
                                           'user_name',
                                           'created_at',
                                           'mentions',
                                           'tags',
                                           'panoptes_project_id',
                                           'response_to_id',
                                           'board_id',
                                           'panoptes_dump']]
    return panoptes_comments

def format_ouroboros_talk(infile,project_df):
    utils.log('loading file: {0}'.format(infile))
    ouroboros_comments = pd.read_csv(infile)
    # create temp series with comments list expanded into individual rows, indexed by discussion
    utils.log('expanding ouroboros discussion list into comments')
    ouroboros_comments_temp = ouroboros_comments.apply(lambda x: pd.Series(json.loads(x['comments'])),axis=1).stack().reset_index(level=1, drop=True)
    # rename the series for merging
    ouroboros_comments_temp.name = 'comment'
    # merge with discussion df
    ouroboros_comments = ouroboros_comments.drop('comments',axis=1).join(ouroboros_comments_temp)
    # rename fields
    ouroboros_comments = ouroboros_comments.rename(columns={'_id':'discussion_id',
                                                            'focus':'discussion_focus',
                                                            'project_id':'ouroboros_mongo_id'})
    # reset the index for expantion of discussion column
    ouroboros_comments = ouroboros_comments.reset_index(drop=True)
    # drop meta columns
    ouroboros_comments = ouroboros_comments[['board',
                                             'discussion_id',
                                             'discussion_focus',
                                             'ouroboros_mongo_id',
                                             'comment']]

    utils.log('formatting comment columns')
    # expand the discussion column into multiple rows
    ouroboros_comments_temp = ouroboros_comments['comment'].apply(pd.Series)
    # rename the _id field
    ouroboros_comments_temp = ouroboros_comments_temp.rename(columns={'_id':'comment_id'})
    # merge discussion meta data with expanded comment df
    ouroboros_comments = ouroboros_comments.merge(ouroboros_comments_temp,right_index=True,left_index=True)
    # drop old comment field
    ouroboros_comments = ouroboros_comments.drop('comment',axis=1)
    utils.log('formatting focus columns')
    # expand the focus column into multiple rows
    ouroboros_comments_temp = ouroboros_comments['discussion_focus'].apply(lambda x: pd.Series(json.loads(x)))
    # rename the _id field and base_type fields
    ouroboros_comments_temp = ouroboros_comments_temp.rename(columns={'_id':'focus_id',
                                                                      'base_type':'focus_base_type'})
    ouroboros_comments_temp = ouroboros_comments_temp[['focus_id','focus_base_type']]
    # merge discussion meta data with expanded comment df
    ouroboros_comments = ouroboros_comments.merge(ouroboros_comments_temp,right_index=True,left_index=True)
    # drop old comment field
    ouroboros_comments = ouroboros_comments.drop('discussion_focus',axis=1)
    utils.log('removing dictionary formatting')
    # remove dictionary formating from comment_id
    ouroboros_comments['comment_id'] = ouroboros_comments['comment_id'].apply(expand_oid_dict_field)
    # remove dictionary formatting from created_at
    ouroboros_comments['created_at'] = ouroboros_comments['created_at'].apply(expand_datetime_dict_field)
    # convert created_at to datetime object
    ouroboros_comments['created_at'] = pd.to_datetime(ouroboros_comments['created_at'])
    # remove dictionary formatting from user_id
    ouroboros_comments['user_id'] = ouroboros_comments['user_id'].apply(expand_oid_dict_field)
    # get id field from board column
    ouroboros_comments['board_id'] = ouroboros_comments['board'].apply(expand_oid_dict_field)
    # merge on ouroboros_mongo_id field to include panoptes id
    ouroboros_comments = ouroboros_comments.merge(project_df[['ouroboros_mongo_id','panoptes_project_id']],
                                                  on='ouroboros_mongo_id')
    # add column for ouroboros info
    ouroboros_comments['ouroboros_dump'] = 1
    # drop columns
    ouroboros_comments = ouroboros_comments[
        ['board_id', 'discussion_id', 'focus_id', 'focus_base_type', 'ouroboros_mongo_id', 'comment_id', 'body',
         'created_at', 'mentions', 'response_to', 'response_to_id', 'tags', 'upvotes', 'user_id', 'user_name',
         'user_zooniverse_id', 'panoptes_project_id', 'ouroboros_dump']]
    return ouroboros_comments

# remove dict keys for dicts stored as string
def expand_text_field(text_field):
    return text_field.split(':')[1].split("'")[1]

# remove dict keys for dicts stored as dict, add ObjectId text for consistancy w/ mongo
def expand_oid_dict_field(dict_field):
    try:
        dict_field = literal_eval(dict_field)
        if '_id' in dict_field:
            return 'ObjectId({0})'.format(dict_field['_id'])
    except ValueError:
        return None
    except TypeError:
        return None

# remove dict keys for dicts stored as dict,    
def expand_datetime_dict_field(dict_field):
    if type(dict_field) == dict:
        return next(iter(dict_field.values()))
    else:
        return None

def mark_project_df(project_df,result_df):
    utils.log('adding talk column to project df')
    project_df.loc[project_df['panoptes_project_id'].isin(result_df['panoptes_project_id']), 'talk'] = 1
    project_df.loc[project_df['talk'].isnull(), 'talk'] = 0
    return project_df

def merge_dfs(panoptes_df,ouroboros_df,project_df):
    utils.log('merging panoptes and ouroboros dfs')
    result_df = ouroboros_df.append(panoptes_df)
    # mark all classifications in the panoptes API == 1
    result_df.loc[result_df['panoptes_project_id'].isin(project_df.loc[project_df['panoptes_api'] == 1]['panoptes_project_id']),'panoptes_api'] = 1
    result_df.loc[result_df['panoptes_project_id'].isin(project_df.loc[project_df['panoptes_api'] == 0]['panoptes_project_id']),'panoptes_api'] = 0
    print(result_df)
    result_df.loc[result_df['panoptes_dump'].isnull(),'panoptes_dump'] = 0
    result_df.loc[result_df['ouroboros_dump'].isnull(),'ouroboros_dump'] = 0
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
    parser.add_argument('--edit_project_df',
                        action='store_true',
                        help='add a talk column to the project df that marks whether the project has talk data')
    args = parser.parse_args()
    project_df = pd.read_csv(args.project)
    ouroboros_comments = format_ouroboros_talk(infile=args.ouroboros,
                                               project_df=project_df)
    panoptes_comments = format_panoptes_talk(infile=args.panoptes)
    result_df = merge_dfs(panoptes_df=panoptes_comments,
                          ouroboros_df=ouroboros_comments,
                          project_df=project_df)
    if args.edit_project_df:
        project_df = mark_project_df(project_df=project_df,
                                     result_df=result_df)
        project_df.to_csv(args.project)
    utils.log('writing file: {0}'.format(args.outfile))
    result_df.to_csv(args.outfile,index=False)
