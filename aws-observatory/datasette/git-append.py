#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""

Checks if the Git repo has new additions to the Observatory, testing for duplicate records
Saves uploaded material into Archives folder
Removes the files with the material to be appended, and pushes the updated database back to the Git repo

"""

#import time
import sqlite3
import pandas as pd
import logging
import os
import shutil
import numpy as np
from datetime import datetime

from git import Repo
#from git import Git

logging.basicConfig(filename='/datasette/database-updates.log', level=logging.INFO)

# Directory settings:

dbrepodir = '/datasette/db-repo/'                 # git repo local dir
archivedir = '/datasette/archives/'               # archive of appended datasets
datasettedir = '/datasette/'                      # datasette dir
git_ssh_identity_file = '/datasette/contributor'  # private key to git repo
repo_url = 'git@github.com:bvitos/greendeal-data.git' # git repo url

# ......

git_ssh_cmd = f'ssh -i {git_ssh_identity_file}'

if os.path.isdir(dbrepodir + '.git/'):           # pull from remote if local repo dir already exists, otherwise clone from remote
    repo = Repo(dbrepodir)
    logging.info(f'{datetime.now().strftime("%Y%m%d_%H%M")} Pulling files from remote repo...')
    logging.info(repo.remotes.origin.pull(env=dict(GIT_SSH_COMMAND=git_ssh_cmd)))
else:
    logging.info(f'{datetime.now().strftime("%Y%m%d_%H%M")} Cloning remote repo...')
    repo = Repo.clone_from(repo_url, dbrepodir, env=dict(GIT_SSH_COMMAND=git_ssh_cmd))
#    repo = Repo(dbrepodir)


dbcon = sqlite3.connect(f'{datasettedir}database.db')
cursor = dbcon.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
if len(tables) > 0:
    dbtables = list(zip(*tables))[0]             # Fetch tables from Observatory database
else:
    dbtables = []                                # New observatory, freshly generated database
logging.info(dbtables)


if True:
    logging.info(f'{datetime.now().strftime("%Y%m%d_%H%M")} Checking for new files...')             # Check for new files
    for file in os.listdir(dbrepodir):
        if file[-3:] == '.db':
            logging.info(f'{datetime.now().strftime("%Y%m%d_%H%M")} Processing {file}.')
            if len(dbtables) > 0:
                newdbcon = sqlite3.connect(file)
                newcursor = newdbcon.cursor()
                newcursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                newtables = newcursor.fetchall()                                                    # Fetch table names from submission
                for table_name in newtables:
                    table_name = table_name[0]
                    if table_name in dbtables:
                        dbtable = pd.read_sql_query("SELECT * from %s" % table_name, dbcon)
                        newtable = pd.read_sql_query("SELECT * from %s" % table_name, newdbcon)
                        if set(newtable.columns.tolist()).issubset(dbtable.columns.tolist()):       # Only process tables that do not contain new columns
                            newtable[list(set(dbtable.columns.tolist()) - set(newtable.columns.tolist()))] = np.nan
                            uniques = pd.merge(newtable,dbtable, indicator=True, how='outer').query('_merge=="left_only"').drop('_merge', axis=1)                   
                            uniques.to_sql(name=table_name, con=dbcon, method='multi', if_exists='append', index = False, chunksize=1000)
                        else:
                            logging.error(f'{datetime.now().strftime("%Y%m%d_%H%M")} New columns detected in table {table_name} - table NOT processed. Please refer to the archives: {archivedir + file[:-3] + datetime.now().strftime("%Y%m%d_%H%M") + ".db"}')
                    else:
                            logging.error(f'{datetime.now().strftime("%Y%m%d_%H%M")} Unexpected table name: {table_name} - table NOT processed. Please refer to the archives: {archivedir + file[:-3] + datetime.now().strftime("%Y%m%d_%H%M") + ".db"}')                        
                newcursor.close()
                newdbcon.close()
            else:
                shutil.copy(dbrepodir + file, datasettedir + 'database.db')                         # If Observatory empty, initialise it with the new file
            shutil.move(dbrepodir + file ,archivedir + file[:-3] + '_' + datetime.now().strftime('%Y%m%d_%H%M') + '.db')
    cursor.close()
    dbcon.close()
    shutil.copy(datasettedir + 'database.db', dbrepodir + 'database/database.db')

try:
    logging.info(repo.git.add(update=True))                                                                           # commit changes and pull
    logging.info(repo.git.commit('-m', 'auto commit'))
    logging.info(f'{datetime.now().strftime("%Y%m%d_%H%M")} Pushing updates to remote repo...')
    repo.remotes.origin.push(env=dict(GIT_SSH_COMMAND=git_ssh_cmd))
except:
    logging.info(f'{datetime.now().strftime("%Y%m%d_%H%M")} No updates pushed to remote repo...')