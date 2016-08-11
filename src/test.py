from panoptes_client import Project,User,Classification,Subject
from pprint import pprint
#pprint (vars(Project.where()))
#pprint (dir(Project.where()))

project_list = Subject.where()
while True:
    x = project_list.next()
    pprint(vars(x))
    break
