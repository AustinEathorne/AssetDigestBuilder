import pathlib, glob, os
from PIL import Image
from directoryHelper import make_dirs

FPS = 15

def generate_gifs(srcDir, dstDir):
  if not os.path.exists(srcDir):
    print(f"No images found to convert to gifs\n")
    return

  print("Generate Gifs")

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
  print(f"Output directory: {dstDir}")
  make_dirs(dstDir)

  # traverse image directories, create gifs (Actor/SetType/Set/*.jpeg)
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
        make_dirs(setTypeDirPath)

        # create gif
        make_gif(animSet.path, animSetFilePath, duration)
        print(f"Create Gif from assets at: {animSet.path}")

        # print progress
        createdGifs += 1
        completion = round((createdGifs/totalGifs) * 100, 2)
        print(f"Progress: {completion}{'%'} ({createdGifs}/{totalGifs})")
        
  print("Gif Conversion Complete\n")

def make_gif(imgSrc, gifDst, duration):
  # get all of the .jpg images in the set directory
  frames = [Image.open(image) for image in glob.glob(f"{imgSrc}/*.JPG")]
  if len(frames) == 0:
    return

  # create gif
  frame_one = frames[0]
  frame_one.save(gifDst,
    format="GIF", append_images=frames, save_all=True, duration=duration, loop=0)

  print(f"Created '{gifDst}'")