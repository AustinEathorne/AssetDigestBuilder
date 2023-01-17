import os

def make_dirs(path):
  if path == "":
    return

  if not os.path.exists(path):
    os.makedirs(path)
    print(f'Created directory at: {path}')

def human_readable_dir_size(path, decimalPlaces = 2):
  return human_readable_size(dir_size(path), decimalPlaces)

def dir_size(path):
  total = 0
  with os.scandir(path) as it:
    for entry in it:
      if entry.is_file():
        total += entry.stat().st_size
      elif entry.is_dir():
        total += dir_size(entry.path)
  return total

def human_readable_size(size, decimal_places = 2):
  for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
    if size < 1024.0 or unit == 'PB':
      break

    size /= 1024.0

  return f"{size:.{decimal_places}f} {unit}"