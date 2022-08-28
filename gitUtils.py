import git

def pull():
    g = git.cmd.Git('sync')
    g.pull()
