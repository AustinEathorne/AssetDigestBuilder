import pathlib, glob, os, shutil
from PIL import Image
from directoryHelper import make_dirs

FPS = 15

def generate_gifs(srcDir, dstDir):
  if not os.path.exists(srcDir):
    print(f"No images found to convert to gifs\n")
    return

  print("Gif Generation Start")

  # duration of each frame in milliseconds
  duration = (1.0/FPS)/0.001  
  
  # get total number of gifs to create
  totalGifs = 0
  for actor in os.scandir(srcDir):
    for setType in os.scandir(actor):
      for animSet in os.scandir(setType):
        if animSet.is_dir():
          totalGifs += 1

  # create destination directory
  make_dirs(dstDir, 1)

  # traverse image directories, create gifs (Actor/SetType/Set/*.jpg)
  createdGifs = 0
  # actors
  for actor in os.scandir(srcDir):
    if not actor.is_dir():
      continue
      
    actorName = pathlib.PurePath(actor.path).name
    actorDirPath = os.path.realpath(os.path.join(dstDir, actorName))

    # set types
    for setType in os.scandir(actor.path):
      if not setType.is_dir():
        continue

      setTypeName = pathlib.PurePath(setType.path).name
      setTypeDirPath = os.path.realpath(os.path.join(actorDirPath, setTypeName))

      # animation sets
      for animSet in os.scandir(setType.path):
        if not animSet.is_dir():
          continue

        animSetName = pathlib.PurePath(animSet.path).name
        animSetFilePath = os.path.realpath(os.path.join(setTypeDirPath, f"{animSetName}.gif"))

        # create output directory
        make_dirs(setTypeDirPath, 1)

        # create gif
        make_gif(animSet.path, animSetFilePath, duration)

        # print progress
        createdGifs += 1
        completion = round((createdGifs/totalGifs) * 100, 2)
        print(f"Progress: {completion}{'%'} ({createdGifs}/{totalGifs})\r", end="")
        
  shutil.rmtree(srcDir)
  print("Gif Generation Complete\n")

def make_gif(imgSrc, gifDst, duration):
  # get all of the .jpg images in the set directory
  frames = [Image.open(image) for image in sorted(glob.glob(f"{imgSrc}/*.jpg"))]
  if len(frames) == 0:
    print(f'\tFailed to create gif, no assets found at: {imgSrc}')
    return

  # create gif
  frame_one = frames[0]
  frame_one.save(gifDst,
    format="GIF", append_images=frames, save_all=True, duration=duration, loop=0)

  print(f"\tCreated '{gifDst}'")