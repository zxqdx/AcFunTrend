__author__ = 'zhangx2'

# Imports parent directory to sys.path
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from miscellaneous import gadget

print(gadget.datetime_to_timestamp())