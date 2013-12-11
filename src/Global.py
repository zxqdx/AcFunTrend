__author__ = "zxqdx"

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from miscellaneous import gadget

wwwPath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
wwwPath = gadget.replace_all(wwwPath, "\\", "/")
