import os
from github import Github

# Workflow Environment Variable Names
MAIN_DIR = "MAIN_DIR"
WIKI_DIR = "WIKI_DIR"
TOOLS_DIR = "TOOLS_DIR"

#PROJ_ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '..',))
#PROJ_CONFIG_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), 'config', 'config.json'))
#PROJ_ASSETS_DIR = os.path.realpath(os.path.join(PROJ_ROOT_DIR, 'Assets'))
#WIKI_REPO_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'solitaire-story.wiki'))
#WIKI_REPO_DIGEST_DIR = os.path.realpath(os.path.join(WIKI_REPO_DIR, 'AssetDigest'))
#WIKI_REPO_ASSETS_DIR = os.path.realpath(os.path.join(WIKI_REPO_DIGEST_DIR, 'Assets'))

def main():
  print("Run Asset Digest Builder")

  # Get location of cloned repos (defined in workflow yaml)
  mainDirPath = get_workflow_environment_var(MAIN_DIR)
  wikiDirPath = get_workflow_environment_var(WIKI_DIR)
  toolsDirPath = get_workflow_environment_var(TOOLS_DIR)

def get_workflow_environment_var(varName):
  var = os.environ.get(varName)
  if varName:
    print(varName)
  else:
    print(f"{varName} environment variable not set")

  return var

if __name__ == '__main__':
  main()