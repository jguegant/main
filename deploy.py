#!/usr/bin/env python

import argparse
from git import Repo
import logging
from subprocess import call

REPO_SUFFIX = '.blog'
LIVE_REPO = 'jguegant.github.io'
BLOG_FOLDER = 'blogs'
OUTPUT_FOLDER = "output"

def checkRepoStatus(repo, name):
    branch = repo.active_branch
    branchName = branch.name

    if branchName != 'master':
        logging.error("You must be on master in [{}] before deployment.".format(name)) 
        return False

    countModifiedFiles = len(repo.index.diff(None))
    countStagedFiles = len(repo.index.diff("HEAD"))
    countUntrackedFiles = len(repo.untracked_files)

    if countStagedFiles > 0 or countModifiedFiles > 0 or countUntrackedFiles > 0:
        logging.error("You must commit everything in [{}] before deployment.".format(name)) 
        return False

    return True

def prepareBlogRepo(name):
    # Let's check if everything has been commited.
    repo = Repo(name)
    
    branch = repo.active_branch
    branchName = branch.name

    if not checkRepoStatus(repo, name):
        return False, ""

    # Let's push master on origin in case.
    logging.info("Pushing [{}].".format(name))
    repo.remotes.origin.push(repo.head)

    # Clean first.
    logging.info("Executing make clean in [{}].".format(name))
    result = call("cd {}; make clean".format(name), shell=True)
    
    if result != 0:
        logging.error("Error while cleaning [{}].".format(name)) 
        return False, ""
    

    logging.info("Executing make publish in [{}].".format(name))
    result = call("cd {}; make publish".format(name), shell=True)

    if result != 0:
        logging.error("Error while publishing [{}].".format(name)) 
        return False, ""

    return True, branch.commit.message + " - " + branch.commit.hexsha


def moveToLiveRepoAndPush(blogName, blogRepoName, lastCommitMessage):
    liveBlogFolder = "./{}/{}/{}".format(LIVE_REPO, BLOG_FOLDER, blogName)
    blogOutputFolder = "./{}/{}".format(blogRepoName, OUTPUT_FOLDER)

    liveRepo = Repo(LIVE_REPO)
    index = liveRepo.index

    if not checkRepoStatus(liveRepo, LIVE_REPO):
        return

    branch = liveRepo.active_branch
    branchName = branch.name


    logging.info("Cleaning {}".format(liveBlogFolder))
    call("rm -rf {}".format(liveBlogFolder), shell=True)

    logging.info("Copying {} into {}".format(blogOutputFolder, liveBlogFolder))
    call("cp -R {} {}".format(blogOutputFolder, liveBlogFolder), shell=True)


    commitMessage = "[Deployement of {}] {}".format(blogRepoName, lastCommitMessage)
    logging.info("Creating a commit for [{}]: {}".format(blogName, commitMessage))
    liveRepo.git.add(BLOG_FOLDER)
    index.commit(commitMessage)

    # Let's push master on origin in case.
    logging.info("Pushing [{}].".format(LIVE_REPO))
    liveRepo.remotes.origin.push(liveRepo.head)


def deployBlog(name):
    logging.info("Deploying the blog [{}]".format(name))
    repoName = name + REPO_SUFFIX
    valid, lastCommitMessage = prepareBlogRepo(repoName)

    if not valid:
        return

    moveToLiveRepoAndPush(name, repoName, lastCommitMessage)


def main():
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
    parser = argparse.ArgumentParser(description='Deploy one of the blog.')
    parser.add_argument('blogname', metavar='NAME', type=str, help='the name of the blog you wish to deploy (tech, personal).', default="tech")

    args = parser.parse_args()

    deployBlog(args.blogname)

main()
