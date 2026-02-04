import os
import sys

# Inject the project root into sys.path to resolve imports within the image-agent package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
