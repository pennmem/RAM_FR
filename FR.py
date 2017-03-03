# COPYRIGHT AND PERMISSION NOTICE
# Penn Neural Recording and Stimulation Software
# Copyright (C) 2015 The Trustees of the University of Pennsylvania. All rights reserved.
#
# SOFTWARE LICENSE
# The Trustees of the University of Pennsylvania ("Penn") and the
# Computational Memory Lab ("Developer") of Penn Neural Recording and Stimulation
# Software ("Software") give recipient ("Recipient") permission to download a
# single copy of the Software in executable form and use for non-profit academic
# research purposes only provided that the following conditions are met:
#
# 1)	Recipient may NOT use the Software for any clinical or diagnostic
#       purpose, including clinical research other than for the purpose of
#       fulfilling Recipient's obligations under the subaward agreement between
#       Penn and Recipient under Prime Award No. N66001-14-2-4-3 awarded by the
#       Defense Advanced Research Projects Agency to Penn ("Subaward").
#
# 2)	Recipient may NOT use the Software for any commercial benefit.
#
# 3)	Recipient will not copy the Software, other than to the extent necessary
#       to fulfill Recipient's obligations under the Subaward.
#
# 4)	Recipient will not sell the Software.
#
# 5)	Recipient will not give the Software to any third party.
#
# 6)	Recipient will provide the Developer with feedback on the use of the
#       Software in their research.  Recipient agrees that the Developers and
#       Penn are freely permitted to use any information Recipient provides in
#       making changes to the Software. All feedback, bug reports and technical
#       questions shall be sent to:
#           Dan Rizzuto: drizzuto@sas.upenn.edu
#
# 7)	Any party desiring a license to use the Software for commercial purposes
#       shall contact:
#           The Penn Center for Innovation at 215-898-9591.
#
# 8)	Recipient will destroy all copies of the Software at the completion of
#       its obligations under its Subaward.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS, CONTRIBUTORS, AND THE
# TRUSTEES OF THE UNIVERSITY OF PENNSYLVANIA "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL THE COPYRIGHT OWNER, CONTRIBUTORS OR THE TRUSTEES OF THE
# UNIVERSITY OF PENNSYLVANIA BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from pyepl import timing

import json
from contextlib import contextmanager

from ramcontrol import wordpool
from ramcontrol.extendedPyepl import *
from ramcontrol.control import RAMControl
from ramcontrol.messages import WordMessage

import playIntro

ram_control = RAMControl.instance()


class FRExperiment(object):
    def __init__(self, exp, config, video, clock):
        """Initialize the data for the experiment. Runs the prepare function,
        sets up the experiment state

        :param Experiment exp:
        :param Config config:
        :param VideoTrack video:
        :param clock:

        """
        self.exp = exp
        self.config = config
        self.subject = exp.getOptions().get('subject')
        self.experiment_name = config.experiment
        self.video = video
        self.clock = clock
        self.wp = CustomTextPool(self.config.wp)

    @property
    def session_started(self):
        """Has the session been started previously?"""
        return self.exp.restoreState().session_started

    @property
    def experiment_started(self):
        """Has the experiment been started previously?"""
        return self.exp.restoreState()

    @property
    def stim_experiment(self):
        """Is this a stim session?"""
        stim_type = self.config.stim_type
        if stim_type == 'CLOSED_STIM':
            return True
        elif stim_type == 'NO_STIM':
            return False
        else:
            raise Exception('STIM TYPE:%s not recognized' % stim_type)

    def init_experiment(self):
        """
        Initializes the experiment, sets up the state so that lists can be run
        :return: state object
        """
        random.seed(self.exp.getOptions().get('subject'))

        self.copy_word_pool()

        # Make the word lists
        session_lists, session_stim = self.prepare_all_sessions_lists()
        practice_lists = self.prepare_practice_lists()

        # Write out the .lst files
        self.write_lst_files(session_lists, practice_lists)

        # Save out the state
        state = self.exp.restoreState()
        self.exp.saveState(state,
                           session_started=False,
                           trialNum=0,
                           practiceDone=False,
                           sessionLists=session_lists,
                           practiceLists=practice_lists,
                           sessionStim=session_stim,
                           lastStimTime=0,
                           sessionNum=0,
                           language='spanish' if self.config.LANGUAGE == 'SP' else 'english',
                           LANG=self.config.LANGUAGE)

        self.exp.setSession(0)
        return self.exp.restoreState()


class FRExperimentRunner(object):
    def __init__(self, experiment, clock, log, mathlog, video, audio):
        self.experiment = experiment
        self.config = experiment.config
        self.clock = clock
        self.log = log
        self.mathlog = mathlog
        self.video = video
        self.audio = audio
        self.start_beep = CustomBeep(
            self.config.startBeepFreq,
            self.config.startBeepDur,
            self.config.startBeepRiseFall)
        self.stop_beep = CustomBeep(
            self.config.stopBeepFreq,
            self.config.stopBeepDur,
            self.config.stopBeepRiseFall)

        # A word is on the screen
        self._on_screen = True

        self._offscreen_callback = None

    def log_message(self, message, time=None):
        """
        Logs a message to the sessionLog file
        :param message: the message to be logged
        :param time: (optional) the time to log with the message
        """
        if not time:
            time = self.clock
        self.log.logMessage(message, time)

    @staticmethod
    def choose_yes_or_no(message):
        """Presents "message" to user

        :return: True if user pressed Y, False if N

        """
        bc = ButtonChooser(Key('Y'), Key('N'))
        _, button, _ = Text(message).present(bc=bc)
        return button == Key('Y')

    def check_sess_num(self, state):
        """
        Prompts the user to check the session number
        :return: True if verified, False otherwise
        """
        subj = self.experiment.subject
        return self.choose_yes_or_no(
            'Running %s in session %d of %s\n(%s).\n Press Y to continue, N to quit' %
            (subj,
             state.sessionNum + 1,
             self.config.experiment,
             state.language))

    @contextmanager
    def state_context(self, state):
        """Context manager to log and send state messages."""
        self.log_message(state + "_START")
        self.send_state_message(state, True)
        yield
        self.send_state_message(state, False)
        self.log_message(state + "_END")

    def send_state_message(self, state, value, meta=None):
        """
        Sends message with STATE information to control pc
        :param state: 'PRACTICE', 'ENCODING', 'WORD'...
        :param value: True/False
        """
        if state not in self.config.state_list:
            raise Exception('Improper state %s not in list of states' % state)
        self.send_event('STATE', state=state, value=value, meta=meta)

    def send_trial_message(self, trial_num):
        """
        Sends message with TRIAL information to control pc
        :param trial_num: 1, 2, ...
        """
        self.send_event('TRIAL', trial=trial_num)

    def send_event(self, type, *args, **kwargs):
        """
        Sends an arbitrary event
        :param args: Inputs to RAMControl.sendEvent()
        """
        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = timing.now()

        if self.config.control_pc:
            ram_control.send(ram_control.build_message(type, *args, **kwargs))

    def show_message_from_file(self, filename):
        """
        Opens a file with utf-8 encoding, displays the message, waits for any key
        :param filenamze: file to be read
        """
        waitForAnyKeyWithCallback(self.clock, Text(codecs.open(filename, encoding='utf-8').read()),
                                  onscreenCallback=lambda: self.send_state_message('INSTRUCT', True),
                                  offscreenCallback=lambda: self.send_state_message('INSTRUCT', False))

    def run_practice_list(self, state):
        """
        Runs a practice list
        :param state: state object
        """
        # Retrieve the list from the state object
        practice_list = state.practiceLists[state.sessionNum]

        # Run the list
        self.log_message('PRACTICE_TRIAL')
        with self.state_context("PRACTICE"):
            self.clock.tare()
            self.run_encoding(practice_list, is_practice=True)

        # Log in state that list has been run
        state.practiceDone = True
        self.experiment.exp.saveState(state)

        # Show a message afterwards
        self.show_message_from_file(self.config.post_practiceList % state.LANG)

    def play_whole_movie(self, movie_file):
        """
        Plays any movie file, centered on the screen.
        """
        movie_object = Movie(movie_file)
        movie_shown = self.video.showCentered(movie_object)
        self.video.playMovie(movie_object)
        self.clock.delay(movie_object.getTotalTime())
        self.clock.wait()
        self.video.stopMovie(movie_object)
        self.video.unshow(movie_shown)

    def countdown(self):
        """Shows the 'countdown' video, centered."""
        self.video.clear('black')
        with self.state_context("COUNTDOWN"):
            self.play_whole_movie(self.config.countdownMovie)

    def on_orient_update(self, *args):
        if self._on_screen:
            self.send_state_message('ORIENT', True)
        else:
            self.send_state_message('ORIENT', False)
            self.send_state_message(self._state_name, True)
        self._on_screen = not self._on_screen

    def run_encoding(self, word_list, state=None, is_stim=False,
                     is_practice=False):
        """Runs a single list of the experiment (encoding phase), presenting
        all of the words in word_list, and logging them as <list_type>_WORD

        :param word_list: words to present
        :param state:
        :param is_stim: whether this list is a stim list
        :param is_practice: (optional) assumes False. True if on practice list

        """
        if not state and not is_practice:
            raise Exception('State not provided on non-practice list')

        if is_practice:
            list_type = 'PRACTICE_'
        else:
            list_type = ''

        if not self.config.fastConfig:
            if not is_practice:
                self.send_trial_message(state.trialNum + 1)
                trial_label = 'trial #%d' % (state.trialNum + 1)
            else:
                self.send_trial_message(-1)
                trial_label = 'practice trial'

            timestamp = waitForAnyKeyWithCallback(
                self.clock,
                Text('Press any key for %s' % trial_label),
                onscreenCallback=lambda: self.send_state_message('WAITING', True),
                offscreenCallback=lambda: self.send_state_message('WAITING', False))
        else:
            timestamp = self.clock
            if is_practice:
                self.send_trial_message(-1)

        if not is_practice:
            self.log_message('TRIAL\t%d\t%s' %
                             (state.trialNum + 1, 'STIM' if is_stim else 'NONSTIM'), timestamp)

        # Need a synchronization close to the start of the list
        self.resynchronize(False)

        # Countdown to start...

        self.countdown()

        # Display the "cross-hairs" and log

        self._state_name = 'STIM ENCODING' if is_stim else 'NON-STIM ENCODING'

        self._on_screen = True
        on_update = self.on_orient_update
        self.video.addUpdateCallback(on_update)
        cbref = self.video.update_callbacks[-1]
        timestamp_on, timestamp_off = flashStimulusWithOffscreenTimestamp(
            Text(self.config.orientText, size=self.config.wordHeight),
            clk=self.clock,
            duration=self.config.wordDuration)
        self.log_message('%sORIENT' % list_type, timestamp_on)
        self.log_message('%sORIENT_OFF' % list_type, timestamp_off)
        # Delay before words
        self.clock.delay(self.config.PauseBeforeWords, jitter=self.config.JitterBeforeWords)
        self.clock.wait()
        self.video.removeUpdateCallback(cbref)

        # ENCODING

        for word_i, word in enumerate(word_list[:-1]):
            self.present_word(word, word_i, is_stim, is_practice)

        # Last word has a callback so it has to be done separately
        self.present_word(word_list[-1], len(word_list) - 1, is_stim, is_practice,
                          offscreen_callback=lambda *args: self.send_state_message(self._state_name, False))

        if self.config.doMathDistract and \
                not self.config.continuousDistract and \
                not self.config.fastConfig:
            self.do_distractor(is_practice)

        self.run_recall(state, is_practice)

    def recall_orient_onscreen_callback(self, *args):
        if not self._orient_sent:
            self.send_state_message('ORIENT', True)
            self._orient_sent = True

    def run_recall(self, state=None, is_practice=False):
        """Runs the recall period of a word list

        :param State state:
        :param bool is_practice: True if list is practice list
        """
        self._orient_sent = False

        # Add a callback and get the reference
        update_callback = self.recall_orient_onscreen_callback
        self.video.addUpdateCallback(update_callback)
        cbref = self.video.update_callbacks[-1]

        # Delay before recall
        self.clock.delay(self.config.PauseBeforeRecall,
                         jitter=self.config.JitterBeforeRecall)
        # Show the recall start indicator
        start_text = self.video.showCentered(Text(self.config.recallStartText,
                                                  size=self.config.wordHeight))

        timestamp = self.video.updateScreen(self.clock)

        # Remove the callback now that the word has been shown
        self.video.removeUpdateCallback(cbref)
        self.log_message('RETRIEVAL_ORIENT', timestamp)

        # Present beep
        self.start_beep.present(self.clock)

        # Hide rec start text
        self.video.unshow(start_text)

        def offscreen_callback(*args):
            self.send_state_message('ORIENT', False)

        self.video.addUpdateCallback(offscreen_callback)
        cbref = self.video.update_callbacks[-1]

        self.video.updateScreen(self.clock)

        self.video.removeUpdateCallback(cbref)

        prefix = 'PRACTICE_' if is_practice else ''
        label = str(state.trialNum) if not is_practice else 'p'

        # Record responses
        (rec, timestamp) = self.audio.record(self.config.recallDuration,
                                             label,
                                             t=self.clock,
                                             startCallback=lambda *args: self.send_state_message('RETRIEVAL', True))

        # Ending beep
        end_timestamp = self.stop_beep.present(self.clock,
                                               onCallback=lambda *args: self.send_state_message('RETRIEVAL', False))

        # Log start and end of recall
        self.log_message('%sREC_START' % prefix, timestamp)
        self.log_message('%sREC_END' % prefix, end_timestamp)

    def on_word_update(self, *args):
        self.send_state_message('WORD', self._on_screen)
        if self._offscreen_callback is not None and not self._on_screen:
            self._offscreen_callback()
        self._on_screen = not self._on_screen

    def present_word(self, word, word_i, is_stim=False, is_practice=False,
                     offscreen_callback=None):
        """Presents a single word to the subject

        :param word: the wordpool object of the word to present
        :param word_i: the serial position of the word in the list
        :param is_stim: Whether or not this is a (potentially) stimulated word
        :param is_practice: Whether this is a practice list

        """
        self._offscreen_callback = offscreen_callback

        # Get the text to present
        word_text = CustomText(word, size=self.config.wordHeight)

        # Delay for a moment
        self.clock.delay(self.config.ISI, self.config.Jitter)
        self.clock.wait()

        self._on_screen = True

        # Send that we're about to display the word
        # Present the word
        timestamp_on, timestamp_off = word_text.presentWithCallback(clk=self.clock,
                                                                    duration=self.config.wordDuration,
                                                                    updateCallback=self.on_word_update)
        # Log that we showed the word
        ram_control.send(WordMessage(word))
        if not is_practice:
            self.log_message(u'WORD\t%s\t%s\t%d\t%s' %
                             ('text', wordpool.remove_accents(word), word_i, 'STIM' if is_stim else 'NO_STIM'),
                             timestamp_on)
            self.log_message(u'WORD_OFF', timestamp_off)
        else:
            self.log_message((u'PRACTICE_WORD\t%s' % word).encode('utf-8'), timestamp_on)
            self.log_message(u'PRACTICE_WORD_OFF', timestamp_off)

        if self.config.continuousDistract:
            self.do_distractor(is_practice)

    def do_distractor(self):
        """Presents the subject with a single distractor period."""
        with self.state_context("DISTRACT"):
            customMathDistract(clk=self.clock,
                               mathlog=self.mathlog,
                               numVars=self.config.MATH_numVars,
                               maxProbs=self.config.MATH_maxProbs,
                               plusAndMinus=self.config.MATH_plusAndMinus,
                               minDuration=self.config.MATH_minDuration,
                               textSize=self.config.MATH_textSize,
                               callback=ram_control.send_math_message)

    def should_skip_session(self, state):
        """Check if session should be skipped

        :return: True if session is skipped, False otherwise

        """
        if self.experiment.session_started:
            bc = ButtonChooser(Key('SPACE') & Key('RETURN'), Key('ESCAPE'))
            self.video.clear('black')
            _, button, timestamp = Text(
                'Session %d was previously started\n' % (state.sessionNum + 1) +
                'Press SPACE + RETURN to skip session\n' +
                'Press ESCAPE to continue'
            ).present(self.clock, bc=bc)
            if 'AND' in button.name:
                self.log_message('SESSION_SKIPPED', timestamp)
                state.sessionNum += 1
                state.trialNum = 0
                state.practiceDone = False
                state.session_started = False
                self.experiment.exp.saveState(state)
                waitForAnyKey(self.clock, Text('Session skipped\nRestart RAM_%s to run next session' %
                                               self.config.experiment))
                return True
        return False

    def resync_callback(self):
        flashStimulus(Text("Syncing..."), 500)

    def resynchronize(self, show_syncing):
        """Performs Christian's algorithm to resync clocks (to be run before
        each list).

        """
        if self.config.control_pc:
            if show_syncing:
                ram_control.align_clocks(callback=self.resync_callback)
            else:
                ram_control.align_clocks()

    def run_all_lists(self, state):
        """
        Runs all of the lists in the given session, read from state
        :param state: State object
        """
        lists = state.sessionLists[state.sessionNum]
        is_stims = state.sessionStim[state.sessionNum]
        while state.trialNum < len(lists):
            this_list = lists[state.trialNum]
            is_stim = is_stims[state.trialNum]
            self.run_encoding([word.name for word in this_list], state, is_stim)
            state.trialNum += 1
            self.experiment.exp.saveState(state)
            self.resynchronize(True)

    def run_recognition(self, state):
        """Run recognition subtask (a.k.a. 'REC1').

        """

    def run_session(self, keyboard):
        """
        Runs a full session of free recall
        """
        config = self.config

        with self.state_context("INSTRUCT"):
            playIntro.playIntro(self.experiment.exp, self.video, keyboard, True, config.LANGUAGE)

        # set priority
        # TODO: What does this do?
        if config.doRealtime:
            setRealtime(config.rtPeriod, config.rtComputation, config.rtConstraint)

        # Get the state object
        state = self.experiment.exp.restoreState()

        # Return if out of sessions
        if self.is_out_of_sessions(state):
            return

        # Set the session appropriately for recording files
        self.experiment.exp.setSession(state.sessionNum)

        # Set the default font
        setDefaultFont(Font(self.config.defaultFont))

        # Clear the screen
        self.video.clear('black')

        if not self.check_sess_num(state):
            sys.exit(1)

        self.video.clear('black')

        stim_type = self.experiment.get_stim_type()
        stim_session_type = '%s_SESSION' % stim_type
        self.log_message('SESS_START\t%s\t%s\tv_%s' % (
                         state.sessionNum + 1,
                         stim_session_type,
                         str(self.config.version)))

        # Reset the list number on the control PC to 0
        self.send_trial_message(-1)
        self.send_event('SESSION', session=state.sessionNum + 1, session_type=stim_type)

        with self.state_context("MIC_TEST"):
            if not customMicTest(2000, 1.0):
                return

        if state.trialNum == 0:
            self.resynchronize(False)
            self.run_practice_list(state)
            self.resynchronize(True)
            state = self.experiment.exp.restoreState()
        
        self.experiment.exp.saveState(state, session_started=True)
        state = self.experiment.exp.restoreState()

        self.run_all_lists(state)

        self.experiment.exp.saveState(state,
                                      trialNum=0,
                                      session_started=False,
                                      sessionNum=state.sessionNum+1,
                                      practiceDone=False)

        timestamp = waitForAnyKey(self.clock, Text('Thank you!\nYou have completed the session.'))
        self.log_message('SESS_END', timestamp)
        self.send_event('EXIT')

        self.clock.wait()

    @staticmethod
    def is_out_of_sessions(state):
        """
        :return: true if all sessions have been run, False otherwise
        """
        return state.sessionNum >= len(state.sessionLists)


def connect_to_control_pc(subject, session, config):
    """
    establish connection to control PC
    """
    if not config.control_pc:
        return
    video = VideoTrack.lastInstance()
    video.clear('black')

    ram_control.configure(config.experiment, config.version, session, config.stim_type, subject, config.state_list)
    clock = PresentationClock()
    if not ram_control.initiate_connection():
        waitForAnyKey(clock,
                      Text("CANNOT SYNC TO CONTROL PC\nCheck connections and restart the experiment",
                           size=.05))
        sys.exit(1)

    cb = lambda: flashStimulus(Text("Waiting for start from control PC..."))
    ram_control.wait_for_start_message(poll_callback=cb)


def run():
    """
    The main function that runs the experiment
    """
    # Start PyEPL, parse command line options
    exp = Experiment(use_eeg=False)
    exp.parseArgs()
    exp.setup()

    # Users can quit with escape-F1
    exp.setBreak()
    RAMControl.instance().register_handler("EXIT", sys.exit)
    RAMControl.instance().socket.log_path = exp.session.fullPath()

    # Get config
    config = exp.getConfig()

    if exp.restoreState():
        session = exp.restoreState().sessionNum
    else:
        session = 0

    # Have to set session before creating tracks
    exp.setSession(session)
    subject = exp.getOptions().get('subject')

    # Set up tracks
    video = VideoTrack('video')
    clock = PresentationClock()

    experiment = FRExperiment(exp, config, video, clock)

    if not experiment.experiment_started:
        state = experiment.init_experiment()
    else:
        state = exp.restoreState()

    log = LogTrack('session')
    mathlog = LogTrack('math')
    audio = CustomAudioTrack('audio')
    keyboard = KeyTrack('keyboard')

    experiment_runner = FRExperimentRunner(experiment, clock, log, mathlog,
                                           video, audio)

    if experiment_runner.should_skip_session(state):
        return

    ram_config_env = json.loads(os.environ["RAM_CONFIG"])
    if not ram_config_env["no_host"]:
        connect_to_control_pc(subject, session, config)
    else:
        print("***** PROCEEDING WITHOUT CONNECTING TO HOST PC! *****")

    experiment_runner.run_session(keyboard)


if __name__ == "__main__":
    run()
