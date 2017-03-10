import os
import subprocess
import argparse
from pymongo import MongoClient

base_dir = r'/srv/zooniverse/raw_data/ouroboros/ouroboros_2016-08-11'

def restore_dumps(base_dir,ignore_file_list):
    # get a list of files from the base directory
    infile_list = [x for x in os.listdir(base_dir) if x not in ignore_file_list]
    for infile in infile_list:
        # strip the file extension from the file name to generate the collection name
        collection_name = infile.replace('.bson','')
        # generate the full file path
        infile_path = os.path.join(base_dir,infile)
        print('importing {0} to {1}'.format(infile_path,collection_name))
        # restore the bson document
        subprocess.run(['mongorestore','-d','zooniverse','-c',collection_name,infile_path])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='import a directory of bson dumps to mongo')
    parser.add_argument('-i','--indir',
                        help='input directory path')
    parser.add_argument('--ignore',
                        nargs='*',
                        default=[
                            'favorites.bson',
                            'projects.bson',
                            'talk.bson',
                            'users.bson',
                            'boards.bson'
                        ],
                        help='a list of .bson files to ignore (including the file extension)')
    args = parser.parse_args()
    restore_dumps(args.indir,args.ignore)
