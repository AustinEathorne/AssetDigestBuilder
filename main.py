import os
#from github import Github
import git
from datetime import datetime
from gifBuilder import generate_gifs
from digestBuilder import generate_markdown_files

# Workflow Environment Variable Names
MAIN_DIR = "MAIN_DIR"
WIKI_DIR = "WIKI_DIR"
TOOLS_DIR = "TOOLS_DIR"
GITHUB_TOKEN = "GITHUB_TOKEN"
GITHUB_WORKSPACE = "GITHUB_WORKSPACE"
#WIKI_REPO_NAME = "AustinEathorne/DigestTest.wiki"
#WIKI_REPO_WORKING_BRANCH = "master"

# Gif Directory Paths (relative to the wiki root directory)
# WikiRoot/Assets/ImagesToConvert/[ActorName]/[SetType]/[AnimSet]/[n].png
WIKI_GIF_SRC_DIR = os.path.realpath(os.path.join("Assets", "ImagesToConvert"))
# WikiRoot/Assets/ActorAnimations/[ActorName]/[SetType]/[AnimSet].gif
WIKI_GIF_OUT_DIR = os.path.realpath(os.path.join("Assets", "ActorAnimations"))

#PROJ_ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '..',))
#PROJ_CONFIG_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), 'config', 'config.json'))
#PROJ_ASSETS_DIR = os.path.realpath(os.path.join(PROJ_ROOT_DIR, 'Assets'))
#WIKI_REPO_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'solitaire-story.wiki'))
#WIKI_REPO_DIGEST_DIR = os.path.realpath(os.path.join(WIKI_REPO_DIR, 'AssetDigest'))
#WIKI_REPO_ASSETS_DIR = os.path.realpath(os.path.join(WIKI_REPO_DIGEST_DIR, 'Assets'))

def main():
  #print("Run Asset Digest Builder")

  # Get environment variables (defined in workflow yaml)
  if (mainDirName := get_environment_var(MAIN_DIR)) is None:
    exit(1)
  if (wikiDirName := get_environment_var(WIKI_DIR)) is None:
    exit(1)
  if (toolsDirName := get_environment_var(TOOLS_DIR)) is None:
    exit(1)
  #if (githubWorkspace := get_environment_var(GITHUB_WORKSPACE)) is None:
    #exit(1)
  #print(f"Github Workspace: {githubWorkspace}")

  startTime = datetime.now()
  print(f"[{startTime.strftime('%H:%M:%S')}] Digest Builder Start\n")

  # build directory paths
  parentDirPath = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
  print(f"Parent Directory: {parentDirPath}")
  repoDirPath = os.path.realpath(os.path.join(parentDirPath, mainDirName))
  print(f"Repo Directory: {repoDirPath}")
  wikiDirPath = os.path.realpath(os.path.join(parentDirPath, wikiDirName))
  print(f"Wiki Directory: {wikiDirPath}")
  toolsDirPath = os.path.realpath(os.path.join(parentDirPath, toolsDirName))
  print(f"Tools Directory: {toolsDirPath}\n")

  print("Directories in Parent: \n")
  for directory in os.scandir(parentDirPath):
    if directory.is_dir():
      print(directory.name)
  print('\n')

  # check if wiki exists
  if os.path.exists(wikiDirPath) == False:
    print('Failed to find wiki repository.')
    exit(1)

  # get the wiki repository
  wikiRepo = git.Repo(wikiDirPath)
  if wikiRepo is None:
    print(f'Failed to retrieve the wiki repository at {wikiDirPath}')
    exit(1)

  # create instance of Github class
  #gh = Github(githubToken)

  # get the wiki repo and branch
  #wikiRepo = gh.get_repo(WIKI_REPO_NAME)
  #wikiBranch = wikiRepo.get_branch(WIKI_REPO_WORKING_BRANCH)

  # generate gifs from animation capture images
  gifSrcDir = os.path.realpath(os.path.join(wikiDirPath, WIKI_GIF_SRC_DIR))
  gifOutDir = os.path.realpath(os.path.join(wikiDirPath, WIKI_GIF_OUT_DIR))
  generate_gifs(gifSrcDir, gifOutDir)

  # search the project for png assets and build markdown files
  print("Generate Markdown Files\n")
  generate_markdown_files(repoDirPath, wikiDirPath)

  # commit and push changes to the wiki repo
  if wikiRepo.is_dirty():
    print("Commit and Push Wiki Changes\n")
    wikiRepo.git.add(".") # Add all local changes
    wikiRepo.index.commit(f'Asset Digest Bump')
    wikiRepo.git.push()
  else:
      print("No changes found in the Wiki repository... something went wrong ^")
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