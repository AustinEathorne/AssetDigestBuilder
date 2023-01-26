import json, os, pathlib, shutil, io
from PIL import Image
#from github import Github
#from urllib.parse import urljoin
from directoryHelper import make_dirs
from imageAsset import ImageAsset

# markdown layout params
MAX_NAME_LENGTH = 22
ASSET_COLUMN_COUNT = 2
ASSET_DISPLAY_SIZE_PERCENTAGE = 100

def generate_markdown_files(repo, repoName, configPath, wikiDir):
  print("Markdown Generation Start")

  mainUrl = 'https://github.com/' + repoName + '/blob/master'
  wikiUrl = 'https://github.com/' + repoName + '/wiki/'
  digestUrl = wikiUrl + 'AssetDigest'

  # load config file from the main repo
  print(f"Looking for config at {configPath}")
  configContent = repo.get_contents(configPath)
  if configContent is None or configContent.type != "file":
    print(f"Failed to find config at: {configPath}")
    exit(1)

  print(configContent.content)
  print("")
  print(configContent.decoded_content)

  fixedConfig = configContent.decoded_content.replace(b"'", b'"')
  print("")
  print(fixedConfig)

  config = json.loads(configContent.decoded_content)

  # create 'AssetDigest' folder in the wiki repo or clear the digest if necessary
  digestDir = os.path.realpath(os.path.join(wikiDir, "AssetDigest"))
  if not make_dirs(digestDir, 1):
    clear_digest(digestDir)

  # create ToC & sidebar markdown file
  tocMd = open(os.path.realpath(os.path.join(digestDir, 'AssetDigest' + '.md')), "w")
  sideBarMd = open(os.path.realpath(os.path.join(wikiDir, '_Sidebar' + '.md')), "w")

  # build paths to asset directories
  mainAssetDir = "Assets"
  digestAssetDir = os.path.realpath(os.path.join(digestDir, "Assets"))

  # traverse project config, write pages
  searchDatas = config['searchData']
  searchDatas.sort(key=lambda searchData: searchData['name'], reverse=False)
  for searchData in config['searchData']:
    process_search_data(searchData, 1, tocMd, sideBarMd, 
      mainAssetDir, mainUrl, wikiUrl,
      digestDir, digestAssetDir, digestDir, digestUrl, repo)

  # close files
  tocMd.close()
  sideBarMd.close()

  print("Markdown Generation Complete\n")

def clear_digest(digestDir):
  # delete all existing md folders, don't want old files to persist if their associated folder/file in the project has changed names
  for file in os.scandir(digestDir):
    if not file.is_dir():
      continue

    # do not clear the assets folder
    if pathlib.Path(file).name == "Assets":
      continue

    shutil.rmtree(file)

def process_search_data(searchData, searchDataHeadingDepth, tocMd, sideBarMd, 
  mainAssetDir, mainUrl, wikiUrl,
  digestRootDir, digestAssetDir, digestMarkdownDir, digestUrl, repo):
  # get search data's name
  searchName = searchData['name']
  print(f'\tProcess search data: {searchName}')

  # add heading to home page for search data
  tocMd.write(searchDataHeadingDepth*"#" + " " + searchName + "\n")
  sideBarMd.write(searchDataHeadingDepth*"#" + " " + searchName + "\n")

  # create a directory for the search data
  digestMarkdownDir = os.path.join(digestMarkdownDir, searchName)
  make_dirs(digestMarkdownDir, 3)

  # process page data, sort directories alphabetically
  pageDatas = searchData['pageData']
  pageDatas.sort(key=lambda pageData: pathlib.Path(pageData['directory']).stem, reverse=False)
  for pageData in pageDatas:
    inProject = pageData['inProject']
    # build the asset's directory path - the asset can reside in either the project or the wiki repo
    if inProject:
      # path is relative to the project's root - Assets/[directory]
      dirPath = f"{mainAssetDir}/{pageData['directory']}"
    else:
      # path is absolute
      dirPath = os.path.realpath(os.path.join(digestAssetDir, pageData['directory']))

    fileExts = pageData['fileExtensions']
    dirDepth = pageData['directoryDepth']
    dirsToExclude = pageData['directoriesToExclude']

    if not os.path.exists(dirPath):
      print(f"\t\tFailed to find directory: {dirPath}")
      continue

    # write page md and add a link to it in the ToC
    if inProject:
      page = write_page_for_main(dirPath, dirDepth, dirsToExclude, fileExts, digestRootDir, repo, wikiUrl, digestUrl)
    else:
      page = write_page_for_wiki(dirPath, dirDepth, dirsToExclude, fileExts, digestRootDir, digestMarkdownDir, wikiUrl, digestUrl)

    tocMd.write(f"- [{page[0]}]({page[1]})\n")
    sideBarMd.write(f"- [{page[0]}]({page[1]})\n")

  tocMd.write("\n")
  sideBarMd.write("\n")

  # process child search data 
  searchDataHeadingDepth += 2
  for sd in searchData['searchData']:
    process_search_data(sd, searchDataHeadingDepth, tocMd, sideBarMd, 
      mainAssetDir, mainUrl, wikiUrl,
      digestRootDir, digestAssetDir, digestMarkdownDir, digestUrl)

# main repo methods
def write_page_for_main(dirPath, dirDepth, dirsToExclude, fileExts, digestDir, digestMarkdownDir, repo, wikiUrl, digestUrl):
  # get nice name
  pageName = pathlib.PurePath(dirPath).name

  # create markdown file
  pagePath = os.path.realpath(os.path.join(digestMarkdownDir, pageName + '.md'))
  pageMd = open(pagePath, "w")
  print(f'\t\tWrite page: {pageName} | path: {pagePath}')

  # write page content
  pageMd.write(f"[Back to Table of Contents]({digestUrl})\n\n")

  # write page assets
  write_page_assets(get_page_assets_for_main(dirPath, fileExts, digestDir), pageMd)
    
  # create sections for all directories found in this directory that aren't excluded
  if dirDepth > 0:
    dirDepth -= 1

    contents = repo.get_contents(dirPath)
    if contents is not None and len(contents) > 0:
      for file in contents:
        if file.type == "dir" and file.name not in dirsToExclude:
          write_page_section_for_main(dirPath, file.name, fileExts, dirDepth, dirsToExclude, pageMd, 1, repo)

  # close file, return page details for the table of contents
  pageMd.close()
  pageUrl = os.path.join(wikiUrl, pageName).replace('\\', '/').replace(' ', '%20')

  return (pageName, pageUrl)

def write_page_section_for_main(dirPath, dirName, fileExts, dirDepth, dirsToExclude, pageMd, headingDepth, repo):
  path = f"{dirPath}/{dirName}"

  # check if the section has assets
  assets = get_page_assets_for_main(path, fileExts, repo)
  hasAssets = False
  for key in assets.keys():
    if len(assets[key]) > 0:
      hasAssets = True
      break

  # write section if it has assets and increase the heading depth
  if hasAssets:
    pageMd.write("\n" + headingDepth*"#" + " " + dirName)
    write_page_assets(assets, pageMd)
    headingDepth += 1

  # create sections for all directories found in this directory that aren't excluded
  if dirDepth > 0:
    dirDepth -= 1
    contents = repo.get_contents(path)
    if contents is not None and len(contents) > 0:
      for file in contents:
        if file.type == "dir" and file.name not in dirsToExclude:
          write_page_section_for_main(path, file.name, fileExts, dirDepth, dirsToExclude, pageMd, headingDepth, repo)

def get_page_assets_for_main(dirPath, fileExts, repo):
  # create asset dictionary
  assets = {}
  for ext in fileExts:
    assets[ext] = []

  # check if path exists
  files = repo.get_contents(dirPath)
  if files == None or len(files) == 0:
    print (f"\t\tFailed to find files in directory: '{dirPath}'")
    return assets

  # gather items of the specified file type in the directory
  print(f"File types found on github at: {dirPath}")
  for file in files:
    # check file type ("dir" or "file")
    print (f"Check: {file.name} | {file.type} | {file.path} | {file.html_url}")
    if file.type == "dir":
      # call this method recursively to get assets within this directory
      #assets.update(get_page_assets_for_main(file.path, fileExts, repo))
      continue
    else:
      # get file extension
      p = pathlib.Path(file.path)
      extension = p.suffix.lower()

      # check if we're looking for this file extension
      if extension in fileExts:
        # create image and determine dimensions
        image = Image.open(io.StringIO(file.decoded_content))
        print(f"Created Image from Repo: {file.name} | width: {image.size[0]} height: {image.size[1]}")
        if image.size[0] >= image.size[1]:
          width = ASSET_DISPLAY_SIZE_PERCENTAGE
          height = (image.size[1] * ASSET_DISPLAY_SIZE_PERCENTAGE)/image.size[0]
        else:
          width = (image.size[0] * ASSET_DISPLAY_SIZE_PERCENTAGE)/image.size[1]
          height = ASSET_DISPLAY_SIZE_PERCENTAGE

        # create ImageAsset and add it to the dictionary
        assets[extension].append(ImageAsset(
          p.name,
          get_abbreviated_asset_name(p.name),
          file.html_url,
          width,
          height))

  # sort alphabetically by name
  assetCount = 0
  for ext in fileExts:
    assets[ext].sort(key=lambda asset: asset.name, reverse=False)
    assetCount += len(assets[ext])

  print(f'\t\t\tFound {assetCount} assets in {dirPath}')

  return assets

# wiki repo methods
def write_page_for_wiki(dirPath, dirDepth, dirsToExclude, fileExts, digestDir, digestMarkdownDir, wikiUrl, digestUrl):
  # get nice name
  pageName = pathlib.PurePath(dirPath).name

  # create markdown file
  pagePath = os.path.realpath(os.path.join(digestMarkdownDir, pageName + '.md'))
  pageMd = open(pagePath, "w")
  print(f'\t\tWrite page: {pageName} | path: {pagePath}')

  # write page content
  pageMd.write(f"[Back to Table of Contents]({digestUrl})\n\n")

  # write page assets
  write_page_assets(get_page_assets_for_wiki(dirPath, fileExts, digestDir, digestUrl), pageMd)
    
  # create sections for all directories found in this directory that aren't excluded
  if dirDepth > 0:
    dirDepth -= 1

    for directory in os.scandir(dirPath):
      if directory.is_dir() and directory.name not in dirsToExclude:
        write_page_section_for_wiki(dirPath, directory.name, fileExts, dirDepth, dirsToExclude, pageMd, 1, digestDir, digestUrl)

  # close file, return page details for the table of contents
  pageMd.close()
  pageUrl = os.path.join(wikiUrl, pageName).replace('\\', '/').replace(' ', '%20')

  return (pageName, pageUrl)

def write_page_section_for_wiki(dirPath, dirName, fileExts, dirDepth, dirsToExclude, pageMd, headingDepth, digestDir, digestUrl):
  path = os.path.join(dirPath, dirName)

  # check if the section has assets
  assets = get_page_assets_for_wiki(path, fileExts, digestDir, digestUrl)
  hasAssets = False
  for key in assets.keys():
    if len(assets[key]) > 0:
      hasAssets = True
      break

  # write section if it has assets and increase the heading depth
  if hasAssets:
    niceName = pathlib.PurePath(path).name
    pageMd.write("\n" + headingDepth*"#" + " " + niceName)
    write_page_assets(assets, pageMd)
    headingDepth += 1

  # create sections for all directories found in this directory that aren't excluded
  if dirDepth > 0:
    dirDepth -= 1
    for directory in os.scandir(path):
      if directory.is_dir() and directory.name not in dirsToExclude:
        write_page_section_for_wiki(path, directory.name, fileExts, dirDepth, dirsToExclude, pageMd, headingDepth, digestDir, digestUrl)

def get_page_assets_for_wiki(dirPath, fileExts, digestDir, digestUrl):
  # create asset dictionary
  assets = {}
  for ext in fileExts:
    assets[ext] = []

  # check if path exists
  if not os.path.exists(dirPath):
    print (f"\t\tFailed to find directory: '{dirPath}'")
    return assets

  # gather items of the specified file type in the directory
  for item in os.scandir(dirPath):
    extension = pathlib.Path(item.path).suffix.lower()
    if extension in fileExts:
      name = item.name.replace(extension)
      title = get_abbreviated_asset_name(name)
      githubUrl = item.path.replace(digestDir, digestUrl).replace('\\', '/').replace(' ', '%20')

      # set image width or height to fit
      image = Image.open(item.path)
      if image.size[0] >= image.size[1]:
        width = ASSET_DISPLAY_SIZE_PERCENTAGE
        height = (image.size[1] * ASSET_DISPLAY_SIZE_PERCENTAGE)/image.size[0]
      else:
        width = (image.size[0] * ASSET_DISPLAY_SIZE_PERCENTAGE)/image.size[1]
        height = ASSET_DISPLAY_SIZE_PERCENTAGE

      assets[extension].append(ImageAsset(name, title, githubUrl, width, height))

  # sort alphabetically by name
  assetCount = 0
  for ext in fileExts:
    assets[ext].sort(key=lambda asset: asset.name, reverse=False)
    assetCount += len(assets[ext])

  print(f'\t\t\tFound {assetCount} assets in {dirPath}')

  return assets

# shared methods
def write_page_assets(assets, pageMd):  
  for key in assets.keys():
    match key:
      case ".png":
        write_images(assets[key], pageMd)
      case ".gif":
        write_images(assets[key], pageMd,)
      case _:
        print(f"\t\tLogic to write \"{key}\" files to markdown is not implemented\n")

def write_images(images, pageMd):
  # write table header
  if len(images) > 0:
    pageMd.write("\n" + "| Asset | Name "*ASSET_COLUMN_COUNT + "|\n")
    pageMd.write("| -- "*(ASSET_COLUMN_COUNT*2) + "|\n")

  # write table elements
  assetCount = 0
  for image in images:
    sizeString = f" width=\"{image.widthPerc}%\" height=\"{image.heightPerc}%\""
    
    # write image
    assetCount += 1
    if assetCount % ASSET_COLUMN_COUNT == 1:
      pageMd.write("|")

    pageMd.write(f" <a href={image.githubUrl}><img src={image.githubUrl} alt={image.name} title={image.name} {sizeString}></a> | {image.title} |")

    if assetCount % ASSET_COLUMN_COUNT == 0:
      pageMd.write("\n")
    if assetCount == len(images) and assetCount % ASSET_COLUMN_COUNT == 1:
      pageMd.write("\n")

def get_abbreviated_asset_name(name):
  if len(name) > MAX_NAME_LENGTH:
    name = name[0 : MAX_NAME_LENGTH - 3]
    name += ".."

  return name