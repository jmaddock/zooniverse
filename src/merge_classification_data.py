
# coding: utf-8

# In[2]:

get_ipython().magic('matplotlib inline')

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
matplotlib.style.use('ggplot')

import requests
import json


# In[79]:

# specify data directory and file
panoptes_data_file = '/srv/zooniverse/tables/panoptes_classification_table_100000.csv'
# read csv file of panoptes classifications
panoptes_classification_df = pd.read_csv(panoptes_data_file,dtype={'user_id':object})
# convert 'created_at' to datetime object
panoptes_classification_df['created_at'] = pd.to_datetime(panoptes_classification_df['created_at'])


# In[80]:

# specify data directory and file
ouroboros_data_file = '/srv/zooniverse/tables/ouroboros_classification_table_100000.csv'
# read csv file of ouroboros classifications
ouroboros_classification_df = pd.read_csv(ouroboros_data_file)
# convert 'created_at' to datetime object
ouroboros_classification_df['created_at'] = pd.to_datetime(ouroboros_classification_df['created_at'])


# In[81]:

# specify project table file
project_table_file = '/srv/zooniverse/tables/all_projects_table_05-19-17.csv'
# load project table
project_df = pd.read_csv(project_table_file)


# In[82]:

# mark all classifications from the panoptes dump
panoptes_classification_df['panoptes_dump'] = 1
# mark all classifications in the ouroboros dump
ouroboros_classification_df['ouroboros_dump'] = 1
# make a df containing only projects found in the API
api_projects = project_df.loc[project_df['panoptes_api'] == 1]


# In[83]:

# mark all classifications in the panoptes API == 1
panoptes_classification_df.loc[panoptes_classification_df['project_id'].isin(api_projects['panoptes_project_id']),'panoptes_api'] = 1
panoptes_classification_df.loc[~panoptes_classification_df['project_id'].isin(api_projects['panoptes_project_id']),'panoptes_api'] = 0


# In[84]:

print(len(panoptes_classification_df.loc[panoptes_classification_df['panoptes_api'] == 1]))
print(len(panoptes_classification_df.loc[panoptes_classification_df['panoptes_api'] == 0]))
assert(len(panoptes_classification_df.loc[panoptes_classification_df['panoptes_api'] == 1]) + len(panoptes_classification_df.loc[panoptes_classification_df['panoptes_api'] == 0]) == len(panoptes_classification_df))


# In[85]:

ouroboros_classification_df = ouroboros_classification_df.rename(columns={'project_id':'ouroboros_mongo_id'})


# In[86]:

ouroboros_classification_df = ouroboros_classification_df.merge(project_df[['ouroboros_mongo_id','panoptes_project_id','panoptes_project_name']],on='ouroboros_mongo_id')


# In[87]:

ouroboros_classification_df.loc[ouroboros_classification_df['panoptes_project_id'].isin(api_projects['panoptes_project_id']),'panoptes_api'] = 1
ouroboros_classification_df.loc[~ouroboros_classification_df['panoptes_project_id'].isin(api_projects['panoptes_project_id']),'panoptes_api'] = 0


# In[88]:

print(len(ouroboros_classification_df.loc[ouroboros_classification_df['panoptes_api'] == 0]))
print(len(ouroboros_classification_df.loc[ouroboros_classification_df['panoptes_api'] == 1]))
assert(len(ouroboros_classification_df.loc[ouroboros_classification_df['panoptes_api'] == 1]) + len(ouroboros_classification_df.loc[ouroboros_classification_df['panoptes_api'] == 0]) == len(ouroboros_classification_df))


# In[89]:

panoptes_classification_df = panoptes_classification_df[['id', 'project_id', 'user_id','created_at','panoptes_dump','panoptes_api']]
panoptes_classification_df = panoptes_classification_df.rename(columns={'id':'classification_id','project_id':'panoptes_project_id'})


# In[90]:

ouroboros_classification_df = ouroboros_classification_df[['_id','created_at','user_name','tutorial','panoptes_project_id','ouroboros_dump','panoptes_api']]
ouroboros_classification_df = ouroboros_classification_df.rename(columns={'_id':'classification_id','user_name':'user_id'})


# In[91]:

result_df = ouroboros_classification_df.append(panoptes_classification_df)


# In[96]:

print(len(result_df.loc[result_df['panoptes_dump'].isnull(),'panoptes_dump']))
print(len(result_df.loc[result_df['panoptes_dump'].notnull(),'panoptes_dump']))


# In[97]:

result_df.loc[result_df['panoptes_dump'].isnull(),'panoptes_dump'] = 0
result_df.loc[result_df['ouroboros_dump'].isnull(),'ouroboros_dump'] = 0


# In[98]:

result_df


# In[ ]:



