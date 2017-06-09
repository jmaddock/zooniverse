
# coding: utf-8

# In[2]:

get_ipython().magic(u'matplotlib inline')

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
matplotlib.style.use('ggplot')

import requests
import json
from ast import literal_eval


# In[3]:

panoptes_comments = pd.read_csv('/srv/zooniverse/raw_data/panoptes/panoptes_comments_2017-03-21.csv')


# In[4]:

panoptes_comments = panoptes_comments.rename(columns={'id':'comment_id',
                                                      'focus_type':'focus_base_type',
                                                      'user_login':'user_name',
                                                      'mentioning':'mentions',
                                                      'tagging':'tags',
                                                      'reply_id':'response_to_id',
                                                      'project_id':'panoptes_project_id'})
panoptes_comments['panoptes_dump'] = 1


# In[5]:

panoptes_comments = panoptes_comments[['comment_id','body','focus_id','focus_base_type','discussion_id','user_id','user_name','created_at','mentions','tags','panoptes_project_id','response_to_id','board_id','panoptes_dump']]


# In[14]:

ouroboros_comments = pd.read_csv('/srv/zooniverse/tables/ouroboros_discussion_table_100000.csv')


# In[16]:

# create temp series with comments list expanded into individual rows, indexed by discussion
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
ouroboros_comments = ouroboros_comments[['board','discussion_id','discussion_focus','ouroboros_mongo_id','comment']]


# In[17]:

# expand the discussion column into multiple rows
ouroboros_comments_temp = ouroboros_comments['comment'].apply(pd.Series)
# rename the _id field
ouroboros_comments_temp = ouroboros_comments_temp.rename(columns={'_id':'comment_id'})
# merge discussion meta data with expanded comment df
ouroboros_comments = ouroboros_comments.merge(ouroboros_comments_temp,right_index=True,left_index=True)
# drop old comment field
ouroboros_comments = ouroboros_comments.drop('comment',axis=1)


# In[18]:

# expand the focus column into multiple rows
ouroboros_comments_temp = ouroboros_comments['discussion_focus'].apply(lambda x: pd.Series(json.loads(x)))
# rename the _id field and base_type fields
ouroboros_comments_temp = ouroboros_comments_temp.rename(columns={'_id':'focus_id','base_type':'focus_base_type'})
ouroboros_comments_temp = ouroboros_comments_temp[['focus_id','focus_base_type']]
# merge discussion meta data with expanded comment df
ouroboros_comments = ouroboros_comments.merge(ouroboros_comments_temp,right_index=True,left_index=True)
# drop old comment field
ouroboros_comments = ouroboros_comments.drop('discussion_focus',axis=1)


# In[19]:

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
    


# In[20]:

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


# In[21]:

# load project csv
project_df = pd.read_csv('/srv/zooniverse/tables/all_projects_table_05-31-17.csv')
# merge on ouroboros_mongo_id field to include panoptes id
ouroboros_comments = ouroboros_comments.merge(project_df[['ouroboros_mongo_id','panoptes_project_id']],on='ouroboros_mongo_id')


# In[38]:

# add column for ouroboros info
ouroboros_comments['ouroboros_dump'] = 1
# drop columns
result_df = ouroboros_comments[['board_id','discussion_id','focus_id','focus_base_type','ouroboros_mongo_id','comment_id','body','created_at','mentions','response_to','response_to_id','tags','upvotes','user_id','user_name','user_zooniverse_id','panoptes_project_id','ouroboros_dump']]


# In[39]:

result_df = result_df.append(panoptes_comments)


# In[49]:

# mark all classifications in the panoptes API == 1
result_df.loc[result_df['panoptes_project_id'].isin(project_df.loc[project_df['panoptes_api'] == 1]['panoptes_project_id']),'panoptes_api'] = 1
result_df.loc[result_df['panoptes_project_id'].isin(project_df.loc[project_df['panoptes_api'] == 0]['panoptes_project_id']),'panoptes_api'] = 0
result_df.loc[result_df['panoptes_dump'].isnull(),'panoptes_dump'] = 0
result_df.loc[result_df['ouroboros_dump'].isnull(),'ouroboros_dump'] = 0


# In[57]:

len(result_df.loc[(result_df['panoptes_dump'] == 1) & (result_df['panoptes_api'] == 1)]['panoptes_project_id'].unique())


# In[ ]:

result_df

