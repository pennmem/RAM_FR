from pyepl.locals import *
import os, shutil

def playIntro(exp, video, keyboard, allowSkip, language):
    """
    Uses the experimental configuration to load a movie and sound clip
    and plays them synchonously with the movie centered on the screen

    (NOTE: video and sound had to be split to allow for playing of files
    that were exported from keynote, which are not compatible with MPEG1 format
    """
    config = exp.getConfig()
    clock = PresentationClock()
    audio = AudioTrack.lastInstance()
    
    video.clear('black')
   
    introMovie = config.introMovie%language
    # if the first list has been completed, allow them to skip playing the movie
    if not allowSkip:
        waitForAnyKey(clock, Text('Press any key to play movie'))
        continueText = Text('Hit SPACE at any time to continue')
        shown = video.showAnchored(continueText,SOUTH,video.propToPixel(.5,1))
        stopBc = ButtonChooser(Key('SPACE'))
        playWholeMovie(video, audio, introMovie, clock, stopBc)
        video.unshow(shown)
        seenOnce = True
    else:
        bc = ButtonChooser(Key('Y'),Key('N'))
        (_,button,_) = Text('Press Y to play instructional video \n Press N continue to practice list').present(bc=bc)
        if button==Key('N'):
            return
        seenOnce = False
    
    bc = ButtonChooser(Key('Y'),Key('N'))

    # Allowed to skip the movie the second time that it has been watched
    while True:
        if seenOnce:
            (_,button,_)=Text('Press Y to continue to practice list, \n Press N to replay instructional video').present(bc = bc)
            if button==Key('Y'):
                break
        continueText = Text('Hit SPACE at any time to continue')
        shown = video.showAnchored(continueText,SOUTH,video.propToPixel(.5,1))
        
        stopBc = ButtonChooser(Key('SPACE'))
        playWholeMovie(video, audio, introMovie,  clock, stopBc)
        seenOnce = True
        video.unshow(shown)


def playWholeMovie(video, audio, movieFile, clock, bc = None):
    """
    Plays any movie file and audio file synchronously
    """
    movieObject = Movie(movieFile)
    movieObject.load()
    video.showCentered(movieObject)
    video.playMovie(movieObject)
    # Stop on button press if BC passed in, otherwise wait until the movie
    # is finished.
    if bc==None:
        clock.delay(movieObject.getTotalTime())
        clock.wait()
    else:
        clock.wait()
        bc.wait()
    video.stopMovie(movieObject)
    movieObject.unload()



# only do this if the experiment is run as a stand-alone program (not imported as a library)
if __name__ == "__main__":
    # make sure we have the min pyepl version
    
    # start PyEPL, parse command line options, and do subject housekeeping
    exp = Experiment(use_eeg = False)
    exp.parseArgs()
    exp.setup()
    
    # allow users to break out of the experiment with escape-F1 (the default key combo)
    exp.setBreak()
    
    # get the full path and try to load the pandaEPL state to get the session number
    # if doesn't exist, then assume session_0
    if exp.restoreState():
        state = exp.restoreState()
        sessionNum = state.sessionNum
        try:
            language = 'SP' if state.language == 'spanish' else 'EN'
        except:
            config=exp.getConfig()
            language = config.LANGUAGE

        try:
            if state.trialNum!=0:
                allowSkip = True
            else:
                allowSkip = False
        except:
            allowSkip = False
    else:
        config = exp.getConfig()
        language = config.LANGUAGE
        sessionNum = 0
        allowSkip = False

    exp.setSession(sessionNum)
    
    video = VideoTrack('video')

    playIntro(exp, video, allowSkip, language) 
    
