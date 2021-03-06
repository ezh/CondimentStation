def _shell():
  from os import environ
  return {'shell': environ['SHELL']}
def _user():
  from getpass import getuser
  return {'user': getuser()}
def _home():
  from getpass import getuser
  from os.path import expanduser
  return {'userhome': expanduser("~" + getuser())}

def main():
  grains = {}
  grains.update(_user())
  grains.update(_shell())
  grains.update(_home())
  return grains
