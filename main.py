import os
#from github import Github
import git
from datetime import datetime
from gifBuilder import generate_gifs
from digestBuilder import generate_markdown_files

# Workflow Environment Variable Names
MAIN_DIR = "MAIN_DIR"
WIKI_DIR = "WIKI_DIR"
GITHUB_SHA = "GITHUB_SHA" #SHA for the commit that triggered the Action (merged to master commit)

# Gif Directory Paths (relative to the wiki root directory)
# WikiRoot/Assets/ImagesToConvert/[ActorName]/[SetType]/[AnimSet]/[n].png
WIKI_GIF_SRC_DIR = os.path.realpath(os.path.join("Assets", "ImagesToConvert"))
# WikiRoot/Assets/ActorAnimations/[ActorName]/[SetType]/[AnimSet].gif
WIKI_GIF_DST_DIR = os.path.realpath(os.path.join("Assets", "ActorAnimations"))


def main():
  startTime = datetime.now()
  print(f"[{startTime.strftime('%H:%M:%S')}] Digest Builder Start\n")

  # get environment variables (defined in workflow yaml)
  if (mainDirName := get_environment_var(MAIN_DIR)) is None:
    exit(1)
  if (wikiDirName := get_environment_var(WIKI_DIR)) is None:
    exit(1)
  if (githubSha := get_environment_var(GITHUB_SHA)) is None:
    exit(1)

  # build directory paths
  parentDirPath = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
  repoDirPath = os.path.realpath(os.path.join(parentDirPath, mainDirName))
  wikiDirPath = os.path.realpath(os.path.join(parentDirPath, wikiDirName))

  # check if wiki exists
  if os.path.exists(wikiDirPath) == False:
    print(f'Failed to find wiki directory repository at: {wikiDirPath}\n')
    exit(1)

  # get the wiki repository
  wikiRepo = git.Repo(wikiDirPath)
  if wikiRepo is None:
    print(f'Failed to retrieve the wiki repository at: {wikiDirPath}\n')
    exit(1)

  # generate gifs from animation capture images
  generate_gifs(
    os.path.realpath(os.path.join(wikiDirPath, WIKI_GIF_SRC_DIR)),
    os.path.realpath(os.path.join(wikiDirPath, WIKI_GIF_DST_DIR)))

  # search the project for png assets and build markdown files
  generate_markdown_files(repoDirPath, wikiDirPath)

  # commit and push changes to the wiki repo
  if wikiRepo.untracked_files:
    print('Adding the following files to git:')
    print([os.path.basename(file) for file in wikiRepo.untracked_files])
    print('\n')
    wikiRepo.git.add(".") # add all local changes

  if wikiRepo.is_dirty():
    print('Commit and push changes to the wiki repo\n')
    wikiRepo.index.commit('-m', 'Asset Digest Bump', '-m', f'Rebuilt the Asset Digest based on commit: {githubSha}')
    wikiRepo.git.push()
  else:
      print("No changes found in the Wiki repository... something went wrong ^\n")
      exit(1)

  # display complete message
  completeTime = datetime.now()
  duration = (completeTime - startTime)
  print(f"[{completeTime.strftime('%H:%M:%S')}] Digest Builder Complete | Duration: {duration}\n")

def get_environment_var(varName):
  var = os.environ.get(varName)
  if var is None:
    print(f"{varName} environment variable not set")

  return var

if __name__ == '__main__':
  main()