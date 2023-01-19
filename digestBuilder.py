import json, os, pathlib, shutil
from PIL import Image
from directoryHelper import make_dirs

# config
CONFIG_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), 'config', 'config.json'))

# urls
REPO_URL = 'https://github.com/AustinEathorne/DigestTest/blob/master' #'https://github.com/uken/solitaire-story/blob/master'
WIKI_URL = 'https://github.com/AustinEathorne/DigestTest/wiki/' #'https://github.com/uken/solitaire-story/wiki/'
ASSET_DIGEST_URL = WIKI_URL + 'AssetDigest'

# markdown layout params
MAX_NAME_LENGTH = 22
ASSET_COLUMN_COUNT = 2
ASSET_DISPLAY_SIZE_PERCENTAGE = 100


def generate_markdown_files(mainDir, wikiDir):
  print("Markdown Generation Start")

  # load the config file
  with open(CONFIG_DIR, 'r') as f:
    config = json.load(f)

  # create 'AssetDigest' folder in the wiki repo if necessary
  digestDir = os.path.realpath(os.path.join(wikiDir, "AssetDigest"))
  make_dirs(digestDir, 1)

  # delete all existing md folders, don't want old files to persist if their associated folder/file in the project has changed names
  for file in os.scandir(digestDir):
    if not file.is_dir():
      continue

    # do not clear the assets folder
    if pathlib.Path(file).name == "Assets":
      continue

    shutil.rmtree(file)

  # create ToC & sidebar markdown file
  tocMd = open(os.path.realpath(os.path.join(digestDir, 'AssetDigest' + '.md')), "w")
  sideBarMd = open(os.path.realpath(os.path.join(wikiDir, '_Sidebar' + '.md')), "w")

  # build ToC page md url
  tocUrl = os.path.join(WIKI_URL, 'AssetDigest').replace('\\', '/')

  # build paths to asset directories
  assetDir = os.path.realpath(os.path.join(mainDir, "Assets"))
  digestAssetDir = os.path.realpath(os.path.join(digestDir, "Assets"))

  # traverse project config, write pages
  searchDatas = config['searchData']
  searchDatas.sort(key=lambda searchData: searchData['name'], reverse=False)
  for searchData in config['searchData']:
    process_search_data(searchData, tocUrl, 1, tocMd, sideBarMd, mainDir, assetDir, digestDir, digestAssetDir, digestDir)

  # close files
  tocMd.close()
  sideBarMd.close()

  print("Markdown Generation Complete\n")

def process_search_data(searchData, tocUrl, searchDataHeadingDepth, tocMd, sideBarMd, mainDir, assetDir, digestDir, digestAssetDir, digestSearchDir):
  # get search data's name
  searchName = searchData['name']
  print(f'\tProcess search data: {searchName}')

  # add heading to home page for search data
  tocMd.write(searchDataHeadingDepth*"#" + " " + searchName + "\n")
  sideBarMd.write(searchDataHeadingDepth*"#" + " " + searchName + "\n")

  # create a directory for the search data
  digestSearchDir = os.path.join(digestSearchDir, searchName)
  make_dirs(digestSearchDir, 3)

  # process page data, sort directories alphabetically
  pageDatas = searchData['pageData']
  pageDatas.sort(key=lambda pageData: pathlib.Path(pageData['directory']).stem, reverse=False)
  for pageData in pageDatas:
    inProject = pageData['inProject']
    # Build the asset's directory path - the asset can reside in either the project or the wiki repo
    dirPath = os.path.realpath(os.path.join(assetDir if inProject else digestAssetDir, pageData['directory']))
    fileExts = pageData['fileExtensions']
    dirDepth = pageData['directoryDepth']
    dirsToExclude = pageData['directoriesToExclude']

    if not os.path.exists(dirPath):
      print(f"\t\tFailed to find directory: {dirPath}")
      continue

    # write page md and add a link to it in the ToC
    page = write_page(dirPath, fileExts, dirDepth, dirsToExclude, inProject, tocUrl, mainDir, digestDir, digestSearchDir)
    tocMd.write(f"- [{page[0]}]({page[1]})\n")
    sideBarMd.write(f"- [{page[0]}]({page[1]})\n")

  tocMd.write("\n")
  sideBarMd.write("\n")

  # process child search data 
  searchDataHeadingDepth += 2
  for sd in searchData['searchData']:
    process_search_data(sd, tocUrl, searchDataHeadingDepth, tocMd, sideBarMd, mainDir, assetDir, digestDir, digestAssetDir, digestSearchDir)

def write_page(dirPath, fileExts, dirDepth, dirsToExclude, inProject, tocUrl, mainDir, digestDir, digestSearchDir):
  # get nice name
  pageName = pathlib.PurePath(dirPath).name

  # create markdown file
  pagePath = os.path.realpath(os.path.join(digestSearchDir, pageName + '.md'))
  pageMd = open(pagePath, "w")
  print(f'\t\tWrite page: {pageName} | path: {pagePath}')

  # write page content
  pageMd.write(f"[Back to Table of Contents]({tocUrl})\n\n")

  # write page assets
  write_page_assets(get_page_assets(dirPath, fileExts), inProject, pageMd, mainDir, digestDir)

  # create sections for all directories found in this directory that aren't excluded
  if dirDepth > 0:
    dirDepth -= 1

    for directory in os.scandir(dirPath):
      if directory.is_dir() and directory.name not in dirsToExclude:
        write_page_section(dirPath, directory, fileExts, dirDepth, dirsToExclude, inProject, pageMd, 1, mainDir, digestDir)

  # close file, return page details for the table of contents
  pageMd.close()

  # build github url
  githubUrl = os.path.join(WIKI_URL, pageName).replace('\\', '/').replace(' ', '%20')

  return (pageName, githubUrl)

def write_page_section(dirPath, dirName, fileExts, dirDepth, dirsToExclude, inProject, pageMd, headingDepth, mainDir, digestDir):
  path = os.path.join(dirPath, dirName)

  # check if the section has assets
  assets = get_page_assets(path, fileExts)
  hasAssets = False
  for key in assets.keys():
    if len(assets[key]) > 0:
      hasAssets = True
      break

  # write section if it has assets and increase the heading depth
  if hasAssets:
    niceName = pathlib.PurePath(path).name
    pageMd.write("\n" + headingDepth*"#" + " " + niceName)
    write_page_assets(assets, inProject, pageMd, mainDir, digestDir)
    headingDepth += 1

  # create sections for all directories found in this directory that aren't excluded
  if dirDepth > 0:
    dirDepth -= 1
    for directory in os.scandir(path):
      if directory.is_dir() and directory.name not in dirsToExclude:
        write_page_section(path, directory, fileExts, dirDepth, dirsToExclude, pageMd, headingDepth)

def get_page_assets(dirPath, fileExts):
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
      assets[extension].append((item.name, item.path))

  # sort alphabetically by name
  assetCount = 0
  for ext in fileExts:
    assets[ext].sort(key=lambda assetPath: pathlib.Path(assetPath[1]).stem, reverse=False)
    assetCount += len(assets[ext])

  print(f'\t\t\tFound {assetCount} assets in {dirPath}')

  return assets

def write_page_assets(assets, inProject, pageMd, mainDir, digestDir):
  for key in assets.keys():
    match key:
      case ".png":
        write_images(key, assets[key], inProject, pageMd, mainDir, digestDir)
      case ".gif":
        write_images(key, assets[key], inProject, pageMd, mainDir, digestDir)
      case _:
        print(f"\t\tLogic for \"{key}\" files is not implemented\n")

def write_images(ext, assets, inProject, pageMd, mainDir, digestDir):
  # write table header
  if len(assets) > 0:
    pageMd.write("\n" + "| Asset | Name "*ASSET_COLUMN_COUNT + "|\n")
    pageMd.write("| -- "*(ASSET_COLUMN_COUNT*2) + "|\n")

  # write table elements
  assetCount = 0
  for asset in assets:
    name = asset[0].replace(ext, "")
    title = get_abbreviated_asset_name(name)
    name = name.replace(' ', '%20')
    githubUrl = asset[1].replace(
      mainDir if inProject else digestDir,
      REPO_URL if inProject else ASSET_DIGEST_URL).replace('\\', '/').replace(' ', '%20')

    # set image width or height to fit
    image = Image.open(asset[1])
    if image.size[0] >= image.size[1]:
      height = (image.size[1] * ASSET_DISPLAY_SIZE_PERCENTAGE)/image.size[0]
      dimensions = f" width=\"{str(ASSET_DISPLAY_SIZE_PERCENTAGE)}%\" height=\"{height}%\""
    else:
      width = (image.size[0] * ASSET_DISPLAY_SIZE_PERCENTAGE)/image.size[1]
      dimensions = f" width=\"{width}%\" height=\"{str(ASSET_DISPLAY_SIZE_PERCENTAGE)}%\""
    
    # write image
    assetCount += 1
    if assetCount % ASSET_COLUMN_COUNT == 1:
      pageMd.write("|")

    pageMd.write(f" <a href={githubUrl}><img src={githubUrl} alt={name} title={name} {dimensions}></a> | {title} |")

    if assetCount % ASSET_COLUMN_COUNT == 0:
      pageMd.write("\n")
    if assetCount == len(assets) and assetCount % ASSET_COLUMN_COUNT == 1:
      pageMd.write("\n")

def get_abbreviated_asset_name(name):
  if len(name) > MAX_NAME_LENGTH:
    name = name[0 : MAX_NAME_LENGTH - 3]
    name += ".."

  return name