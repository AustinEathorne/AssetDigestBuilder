import os, git, textwrap
from datetime import datetime
from gifBuilder import generate_gifs
from digestBuilder import generate_markdown_files

# Workflow Environment Variable Names
MAIN_DIR = "MAIN_DIR"
WIKI_DIR = "WIKI_DIR"
GITHUB_SHA = "GITHUB_SHA" #SHA for the commit that triggered the Action (merged to master commit)

# Gif Directory Paths (relative to the wiki root directory)
# WikiRoot/AssetDigest/Assets/ImagesToConvert/[ActorName]/[SetType]/[AnimSet]/[n].png
WIKI_GIF_SRC_DIR_NAME = "ImagesToConvert"
# WikiRoot/AssetDigest/Assets/ActorAnimations/[ActorName]/[SetType]/[AnimSet].gif
WIKI_GIF_DST_DIR_NAME = "ActorAnimations"


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
    os.path.realpath(os.path.join(wikiDirPath, "AssetDigest", "Assets", WIKI_GIF_SRC_DIR_NAME)),
    os.path.realpath(os.path.join(wikiDirPath, "AssetDigest", "Assets", WIKI_GIF_DST_DIR_NAME)))

  # search the project for png assets and build markdown files
  generate_markdown_files(repoDirPath, wikiDirPath)

  # commit and push changes to the wiki repo
  print('Update Wiki Repo')
  if wikiRepo.untracked_files:
    print('\tAdding the following files to git:')
    print(textwrap.indent('\n'.join([os.path.basename(file) for file in wikiRepo.untracked_files]), '\t\t'))
  
  wikiRepo.git.add(".") # add all local changes

  if wikiRepo.is_dirty():    
    print('\t Changes:')
    for file in wikiRepo.git.diff('--name-only').split():
      print(f'\t\t{file}')
    
    print('\t Changes:')
    print(textwrap.indent('\n'.join(wikiRepo.git.diff('--name-only').split()), '\t\t')) #TODO this prints nothing

    wikiRepo.index.commit(f'Update Asset Digest based on commit: {githubSha}')
    wikiRepo.git.push()
  else:
    print("\tNo changes found in the Wiki repository\n")

  # display complete message
  completeTime = datetime.now()
  duration = (completeTime - startTime)
  print(f"[{completeTime.strftime('%H:%M:%S')}] Digest Builder Complete | Duration: {duration}")

def get_environment_var(varName):
  var = os.environ.get(varName)
  if var is None:
    print(f"{varName} environment variable not set")

  return var

if __name__ == '__main__':
  main()