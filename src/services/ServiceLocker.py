'''
Created on Dec 8, 2013

@author: zxqdx
'''

# Imports parent directory to sys.path
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from miscellaneous import gadget
import Global

class ServiceLocker(object):
    """
    Create locks for service to ensure that ONLY one service is running at one time.
    """

    def __init__(self, serviceName):
        self.serviceName = serviceName
        self.serviceLockPath = "{}.{}".format(serviceName, Global.lockFileSuffix)
        self._check()

    def _check(self):
        if gadget.is_file(self.serviceLockPath):
            raise IOError("{} already exists. This might because another instance of {} is running.".format(
                self.serviceLockPath, self.serviceName))

    @staticmethod
    def _raise(msg):
        raise Exception(msg)

    def acquire(self):
        gadget.try_until_sign_appears(None, lambda: gadget.write_file(self.serviceLockPath, 1),
                                      failedFunc=lambda: self._raise("Failed to acquire lock."), retryNum=5)

    def release(self):
        gadget.try_until_sign_appears(None, lambda: gadget.remove_file(self.serviceLockPath),
                                      failedFunc=lambda: self._raise("Failed to release lock."), retryNum=5)
