import logging
import git
from pathlib import Path

import self as self
from git import Repo
PATH_FOR_DATA = Path("./data-for-designer")
PATH_FOR_GIT = Path("./data-for-designer/.git")

def git_init():
    try:
        repo = git.Repo.clone_from('http://172.20.41.70:3000/SPTeam/data-for-designer.git',
                                   './data-for-designer',branch='main')
    except Exception as e:
        logging.warning('GIT Push 에러 발생' + e)


def git_push():
    try:
        repo = git.Repo(PATH_FOR_GIT)
        repo.git.checkout('main')
        origin = repo.remotes.origin
        origin.pull()
        # repo.git.stash('save')
        # repo.git.reset('--hard')
        # repo.git.stash('pop')
        repo.git.add(all=True)
        repo.index.commit('Feat: Auto Push from python')
        origin.push()

    except Exception as e:
        logging.warning('GIT Push 에러 발생' + e)

if PATH_FOR_GIT.exists():
    git_push()
else :
    git_init()







