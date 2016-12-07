#!/usr/bin/python
from pyepl.locals import *
def skip_session(exp):
    # create tracks
    state = exp.restoreState()
    exp.setSession(state.sessionNum)

    video = VideoTrack("video")
    keyboard = KeyTrack("keyboard")
    log = LogTrack("session")
    mathlog = LogTrack("math")

    continueKey=Key('SPACE')&Key('RETURN')
    breakKey = Key('ESCAPE')

    message = Text('Press SPACE and RETURN \n to skip session %d.\n Press esc to exit without skipping.'%state.sessionNum)
    bc = ButtonChooser(continueKey, breakKey)
    
    video.showCentered(message)
    video.updateScreen()
    b = bc.wait()

    if b==continueKey:
        print 'skipping session...'
        state.sessionNum +=1 
        state.trialNum = 0
        exp.saveState(state)
        log.logMessage('SESSION_SKIPPED',PresentationClock().get())

    

# only do this if the experiment is run as a stand-alone program (not imported 
# as a library)
if __name__ == "__main__":

    
    # start PyEPL, parse command line options, and do subject housekeeping
    exp = Experiment()

    # Skip the current session
    skip_session(exp)

