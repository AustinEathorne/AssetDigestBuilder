import os, git, textwrap
from github import Github
from datetime import datetime
from gifBuilder import generate_gifs
from digestBuilder import generate_markdown_files

# Workflow Environment Variable Names
#MAIN_DIR = "MAIN_DIR"
WIKI_DIR = "WIKI_DIR"
GITHUB_TOKEN = "GITHUB_TOKEN" # access token for the main repo
GITHUB_SHA = "GITHUB_SHA" #SHA for the commit that triggered the Action (merged to master commit)
REPO_NAME = "REPO_NAME" # the name of the repo to operate on
CONFIG_PATH = "CONFIG_PATH" # path to the config file in the main repo

# Gif Directory Paths (relative to the wiki root directory)
# WikiRoot/AssetDigest/Assets/ImagesToConvert/[ActorName]/[SetType]/[AnimSet]/[n].png
WIKI_GIF_SRC_DIR_NAME = "ImagesToConvert"
# WikiRoot/AssetDigest/Assets/ActorAnimations/[ActorName]/[SetType]/[AnimSet].gif
WIKI_GIF_DST_DIR_NAME = "ActorAnimations"


def main():
  # display start message
  startTime = datetime.now()
  print(f"[{startTime.strftime('%H:%M:%S')}] Digest Builder Start\n")

  # get environment variables (defined in workflow yaml)
  #if (mainDirName := get_environment_var(MAIN_DIR)) is None:
    #exit(1)
  if (wikiDirName := get_environment_var(WIKI_DIR)) is None:
    exit(1)
  if (githubToken := get_environment_var(GITHUB_TOKEN)) is None:
    exit(1)
  if (githubSha := get_environment_var(GITHUB_SHA)) is None:
    exit(1)
  if (repoName := get_environment_var(REPO_NAME)) is None:
    exit(1)
  if (configPath := get_environment_var(CONFIG_PATH)) is None:
    exit(1)

  # initialize github obj with access token
  gh = Github(githubToken)

  # get the main repo
  repo = gh.get_repo(repoName) # OWNER/REPO_NAME format
  if repo is None:
    print(f"Failed to find the repo: {repoName}")
    exit(1)
  #content = repo.get_contents(path)

  # get the wiki directory path and git repo
  wikiDirPath = get_wiki_directory_path(repoName, wikiDirName)
  wikiRepo = get_wiki_repo(wikiDirPath)

  # generate gifs, build digest, commit and push
  generate_gifs_from_images(wikiDirPath, wikiRepo)
  generate_markdown_files(repo, repoName, configPath, wikiDirPath)
  commit_and_push_changes(wikiRepo, githubSha)

  # display complete message
  completeTime = datetime.now()
  duration = (completeTime - startTime)
  print(f"[{completeTime.strftime('%H:%M:%S')}] Digest Builder Complete | Duration: {duration}")

def get_environment_var(varName):
  var = os.environ.get(varName)
  if var is None:
    print(f"{varName} environment variable not set")

  return var

def get_wiki_directory_path(wikiDirName):
  parentDirPath = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
  wikiDirPath = os.path.realpath(os.path.join(parentDirPath, wikiDirName))
  return wikiDirPath

def get_wiki_repo(wikiDirPath):
  # check if wiki exists
  if os.path.exists(wikiDirPath) == False:
    print(f'Failed to find wiki directory repository at: {wikiDirPath}\n')
    exit(1)

  # get the wiki repository
  wikiRepo = git.Repo(wikiDirPath)
  if wikiRepo is None:
    print(f'Failed to retrieve the wiki repository at: {wikiDirPath}\n')
    exit(1)

  return wikiRepo

def generate_gifs_from_images(wikiDirPath, wikiRepo):
  # check if there are images to convert
  gifSrcDir = os.path.realpath(os.path.join(wikiDirPath, "AssetDigest", "Assets", WIKI_GIF_SRC_DIR_NAME))
  if not os.path.exists(gifSrcDir):
    print(f"No images found to convert to gifs\n")
    return

  # generate gifs from animation capture images
  generate_gifs(
    gifSrcDir,
    os.path.realpath(os.path.join(wikiDirPath, "AssetDigest", "Assets", WIKI_GIF_DST_DIR_NAME)))

  # remove gif src files
  for file in os.scandir(gifSrcDir):
    wikiRepo.git.rm("-r", file.path)

def commit_and_push_changes(wikiRepo, githubSha):
  print('Update Wiki Repo')

  # print new files
  if wikiRepo.untracked_files:
    print('\tAdding the following files to git:')
    print(textwrap.indent('\n'.join([os.path.basename(file) for file in wikiRepo.untracked_files]), '\t\t'))
  
  # add all local changes
  wikiRepo.git.add(".")

  # commit and push changes to the wiki repo
  if wikiRepo.is_dirty():
    wikiRepo.index.commit(f'Updated Asset Digest based on commit: {githubSha}')
    wikiRepo.git.push()
    print("\tChanges committed and pushed\n")
  else:
    print("\tNo changes found in the Wiki repository\n")

if __name__ == '__main__':
  main()