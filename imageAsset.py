from dataclasses import dataclass

@dataclass
class ImageAsset: #TODO move
  name: str
  title: str
  githubUrl: str
  widthPerc: float
  heightPerc: float
