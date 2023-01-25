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
  wikiRepo = gh.get_repo(repoName + '/wiki')

  # null check repos
  if repo is None:
    print(f"Failed to get the main repo with name {repoName}")
    exit(1)

  if wikiRepo is None:
    print(f"Failed to get the wiki repo with name {repoName}/wiki")
    exit(1)

  # get and print contents
  contents = get_contents(repo, "Assets/Images")
  print_contents(contents)
  wikiContents = get_contents(wikiRepo, "AssetDigest/Assets/")
  print_contents(wikiContents)

  print("Test Complete")

def get_environment_var(varName):
  var = os.environ.get(varName)
  if var is None:
    print(f"{varName} environment variable not set")
  return var

def get_contents(repo, path):
  contents = repo.get_contents(path)
  if contents is None or len(contents) == 0:
    print(f"Failed to get contents in the main repo at {path}")
    exit(1)

  return contents

def print_contents(contents):
  for file in contents:
    if file.type == "dir":
      print(f"Found directory: {file.name} at {file.path}\nURL: {file.html_url}\n")
    else:
      print(f"Found file: {file.name} of type {file.type} at {file.path}\nURL: {file.html_url}\n")

if __name__ == '__main__':
  test()