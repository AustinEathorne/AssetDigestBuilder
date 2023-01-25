import os
from github import Github

GITHUB_TOKEN = "GITHUB_TOKEN" # access token for the main repo
REPO_NAME = "REPO_NAME" # the name of the repo to operate on


def test():
  print("Run Test\n")

  # get environment variables
  if (githubToken := get_environment_var(GITHUB_TOKEN)) is None:
    exit(1)
  if (repoName := get_environment_var(REPO_NAME)) is None:
    exit(1)

  # initialize github class and get repos
  gh = Github(githubToken)
  repo = gh.get_repo(repoName)
  #wikiRepo = gh.get_repo(repoName + '/wiki')

  # null check repos
  if repo is None:
    print(f"Failed to get the main repo with name {repoName}")
    exit(1)

  #if wikiRepo is None:
  #  print(f"Failed to get the wiki repo with name {repoName}/wiki")
  #  exit(1)

  # get and print contents
  contents = get_contents(repo, "Assets/Images")
  print_contents(repo, contents)
  #wikiContents = get_contents(wikiRepo, "AssetDigest/Assets/")
  #print_contents(wikiContents)

  print("Test Complete")

def get_environment_var(varName):
  var = os.environ.get(varName)
  if var is None:
    print(f"{varName} environment variable not set")
  else:
    print(f"Got environment var {varName}: {var}")
  return var

def get_contents(repo, path):
  contents = repo.get_contents(path)
  if contents is None or len(contents) == 0:
    print(f"Failed to get contents in the main repo at {path}")
    exit(1)

  return contents

def print_contents(repo, contents):
  for file in contents:
    print(f"Found: {file.name} | type: {file.type} | path: {file.path}\nURL: {file.html_url}")

    if file.type == "dir":
      print_contents(repo, get_contents(repo, file.path))
    else:
      print(' ')

if __name__ == '__main__':
  test()