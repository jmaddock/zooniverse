import os
import subprocess
import shutil
import argparse
import pandas as pd
from pymongo import MongoClient

def export_dumps(db_name,collection_type,outdir,field_file):
    client = MongoClient()
    # get a list of all collection in the database that have collection_type in the name
    collections_list = [x for x in client['zooniverse'].collection_names() if collection_type in x]
    # the path of a temp directory to export files from mongo
    tempdir = os.path.join(outdir,'temp')
    # if the temp directory doesn't already exist, create it
    if not os.path.exists(tempdir):
        os.mkdir(tempdir)

    for collection in collections_list:
        temp_outfile = os.path.join(tempdir,'{0}.csv'.format(collection))
        print('exporting {0} to {1}'.format(collection,temp_outfile))
        # run mongoexport to generate a .csv file in the temp directory
        subprocess.run(['mongoexport','-d',db_name,'-c',collection,'--fieldFile',field_file,'--type=csv','--out',temp_outfile])

def combine_dumps(outdir,project_df_dir):
    tempdir = os.path.join(outdir,'temp')
    infile_list = os.listdir(tempdir)
    outfile = pd.DataFrame()
    project_df = pd.read_csv(project_df_dir)
    for infile in infile_list:
        project_title = infile.rsplit('_',1)[0]
        print('loading project {0} from {1}'.format(project_title,os.path.join(tempdir,infile)))
        # read the temp csv
        df = pd.read_csv(os.path.join(tempdir,infile))
        df['project_name'] = project_title
        try:
            df['project_id'] = project_df.loc[project_df['name'] == project_title,'_id'].values[0]
        except IndexError:
            print('no project {0}'.format(infile.replace('.csv','')))
        outfile = outfile.append(df)
    return outfile

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='import a directory of bson dumps to mongo')
    parser.add_argument('-o','--outfile',
                        help='output directory path')
    parser.add_argument('-f','--field_file',
                        help='a .txt file of fields to export')
    parser.add_argument('-t','--collection_type',
                        choices=['classifications','subjects','groups'],
                        help='the type of db to export')
    parser.add_argument('-p','--project_table',
                        help='a path to a .csv file containing information about ouroboros projects')
    parser.add_argument('-d','--db_name',
                        help='the name of the mongodb containing all collections')
    parser.add_argument('--ignore',
                        nargs='*',
                        help='a list of collection names to ignore (including the file extension)')
    parser.add_argument('--dump',
                        action='store_true',
                        help='export collections from mongo')
    parser.add_argument('--combine',
                        action='store_true',
                        help='combine the exported collections into a single csv')
    args = parser.parse_args()
    outdir = os.path.dirname(args.outfile)
    if args.dump:
        export_dumps(db_name=args.db_name,
                     collection_type=args.collection_type,
                     outdir=outdir,
                     field_file=args.field_file)
    if args.combine:
        df = combine_dumps(outdir=outdir,
                           project_df_dir=args.project_table)
        print('writing file {0}'.format(args.outfile))
        df.to_csv(args.outfile)

   # print('cleaning up directory {0}'.format(os.path.join(outdir,'temp')))
   # shutil.rmtree(os.path.join(outdir,'temp'))
    

