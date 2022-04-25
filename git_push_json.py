import logging
import git
from pathlib import Path

PATH_FOR_GIT = Path(".git")

def find_repo(path):
    "Find repository root from the path's parents"
    for path in Path(path).parents:
        # Check whether "path/.git" exists and is a directory
        git_dir = path / ".git"
        if git_dir.is_dir():
            return path

def git_push():
    try:
        repo_path = find_repo(__file__)
        repo = git.Repo(repo_path)
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
    logging.warning('GIT설정을 확인해주세요.')






