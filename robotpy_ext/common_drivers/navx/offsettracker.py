# validated: 2017-02-19 DS 83e16a18b59e roborio/java/navx_frc/src/com/kauailabs/navx/frc/OffsetTracker.java
#----------------------------------------------------------------------------
# Copyright (c) Kauai Labs 2015. All Rights Reserved.
#
# Created in support of Team 2465 (Kauaibots).  Go Purple Wave!
#
# Open Source Software - may be modified and shared by FRC teams. Any
# modifications to this code must be accompanied by the \License.txt file
# in the root directory of the project
#----------------------------------------------------------------------------

from collections import deque

class OffsetTracker:
    
    def __init__(self, history_length):
        self.value_history = deque([0]*history_length, maxlen=history_length)
        self.value_offset = 0
    
    def updateHistory(self, value):
        self.value_history.append(value)

    def getAverageFromHistory(self):
        return sum(self.value_history) / float(len(self.value_history))
    
    def setOffset(self):
        self.value_offset = self.getAverageFromHistory()
    
    def getOffset(self):
        return self.value_offset
    
    def applyOffset(self, value):
        offseted_value = (value - self.value_offset)
        if offseted_value < -180:
            offseted_value += 360
        
        if offseted_value > 180:
            offseted_value -= 360
        
        return offseted_value
