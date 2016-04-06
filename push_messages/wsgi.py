import os

from paste.deploy import loadapp


parent_dir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))

application = loadapp('config:production.ini', relative_to=parent_dir)
