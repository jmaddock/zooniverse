from panoptes_client import Project,User,Classification,Subject,Workflow,Panoptes
from panoptes_client.panoptes import Talk
from pprint import pprint
#pprint (vars(Project.where()))
#pprint (dir(Project.where()))

# get a list of projects

'''
project_list = Project.where()
count = 0
while count < 1:
    project = project_list.next()
    pprint(vars(project))
    # get a list of subjects (images) for classification
    subject_list = Subject.where(slug=project.raw['slug'])
    while count < 1:
        subject = subject_list.next()
        count += 1
        pprint(vars(subject))
    #pprint(vars(x.links))
    
    #print(x._api_slug)
    #project = Project.find(slug=)


user_list = User.where()
count = 0
while count < 1:
    user = user_list.next()
    pprint(vars(user))
    # get a list of subjects (images) for classification
    count += 1


classification_list = Classification.where(slug='zooniverse/snapshot-supernova')
count = 0
while count < 1:
    classification = classification_list.next()
    pprint(vars(classification))
    # get a list of subjects (images) for classification
    count += 1
'''

talk_list = p.Talk.get()
count = 0
while count < 1:
    talk = talk_list.next()
    pprint(vars(talk))
    # get a list of subjects (images) for classification
    count += 1
