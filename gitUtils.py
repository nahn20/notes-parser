import git
import pathlib
import os

def pull():
    path = os.path.join(pathlib.Path(__file__).parent.resolve(), 'sync')
    g = git.cmd.Git(path)
    g.pull()
