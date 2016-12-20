#!/usr/bin/python

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

from extendedPyepl import *

import logging
import codecs  # FOR READING UNICODE
import random
import os
import sys
import shutil
import unicodedata
import playIntro
from log import setup_logging
from RAMControl import RAMControl
from messages import WordMessage

ram_control = RAMControl.instance()

# Set the current version
# TODO: Update the version for System 2.0 pyepl changes
MIN_PYEPL_VERSION = '1.0.0'


class Utils:

    def __init__(self):
        pass

    @staticmethod
    def shuffle_together(*lists):
        zipped_lists = zip(*lists)
        random.shuffle(zipped_lists)
        return zip(*zipped_lists)

    @staticmethod
    def shuffle_inner_lists(lists):
        """
        Shuffles items within each list in place
        :param lists: 2D list of size nLists x wordsPerList
        """
        for l in lists:
            random.shuffle(l)

    @staticmethod
    def seed_rng(seed):
        """
        Seeds the random number generator with the input argument
        :param seed: the element to seed Random with
        """
        random.seed(seed)

    @staticmethod
    def remove_accents(input_str):
        nkfd_form = unicodedata.normalize('NFKD', input_str)
        return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])


class FRExperiment:

    def __init__(self, exp, config, video, clock,):
        """
        Initialize the data for the experiment.
        Runs the prepare function, sets up the experiment state
        :param exp: Experiment object
        :param config: Config object
        :param video: VideoTrack object
        """
        self.exp, self.config = \
            exp, config
        self.subject = exp.getOptions().get('subject')
        self.experiment_name = config.experiment
        self.video = video
        self.clock = clock
        self.wp = CustomTextPool(self.config.wp)

    def _show_prepare_message(self):
        """
        Shows "Preparing trials in..."
        """
        self.video.clear('black')
        self.video.showCentered(Text(
            """
** PREPARING TRIALS IN %(language)s **
If this is not correct,
exit the experiment,
then delete the subject folder in:
/Users/exp/RAM_2.0/data/%(exp)s/%(subj)s
        """ % {'language': 'ENGLISH' if self.config.LANGUAGE == 'EN' else 'SPANISH',
               'exp': self.experiment_name,
               'subj': self.subject}))
        self.video.updateScreen()
        self.clock.delay(1000)
        self.clock.wait()

    def _copy_word_pool(self):
        """
        Copies the word pool with and without accents to session folder
        """
        sess_path = self.exp.session.fullPath()
        # With accents
        shutil.copy(self.config.wp, os.path.join(sess_path, '..'))
        # Without accents
        no_accents_wp = [Utils.remove_accents(line.strip())
                         for line in codecs.open(self.config.wp, 'r', 'utf-8').readlines()]
        open(os.path.join(sess_path,'..', self.config.noAcc_wp), 'w').write('\n'.join(no_accents_wp))

    def _assert_good_list_params(self):
        assert self.config.numTrials == (self.config.nBaselineTrials +
                                         self.config.nStimTrials +
                                         self.config.nControlTrials)

    def _verify_files(self):
        """
        Verify that all the files specified in the config are there so
        that there is no random failure in the middle of the experiment.

        This will call sys.exit(1) if any of the files are missing.
        """
        config = self.config
        if config.LANGUAGE != 'EN' and config.LANGUAGE != 'SP':
            print '\nERROR:\nLanguage must be set to "EN" or "SP"'
            sys.exit(1)

        # make the list of files from the config vars
        files = (config.wp,
                 config.defaultFont,
                 config.pre_practiceList % config.LANGUAGE,
                 config.post_practiceList % config.LANGUAGE,
                 config.practice_wordList % config.LANGUAGE,
                 config.wordList_dir % config.LANGUAGE
                 )

        for f in files:
            if not os.path.exists(f):
                print "\nERROR:\nPath/File does not exist: %s\n\nPlease verify the config.\n" % f
                sys.exit(1)

    def _get_stim_session_sources(self):
        """
        will return the filenames to be read for all sessions
        that are counterbalanced for stim positions
        :return: the filenames for each session
        """
        sess_numbers = [[i, i+1] for i in range(1, self.config.numSessions+1, 2)]
        print(sess_numbers)
        random.shuffle(sess_numbers)
        session_sources = []
        for sess_pair in sess_numbers:
            random.shuffle(sess_pair)
            session_sources.extend(
                [os.path.join(self.config.wordList_dir % self.config.LANGUAGE,
                              '%d.txt' % sess_num)
                    for sess_num in sess_pair])
        return session_sources

    def _get_nonstim_session_sources(self):
        """
        Gets the filenames to be read for all sessions to be
        used for the non-stim experiment
        :return: the filename for each session
        """
        session_sources = range(1, self.config.numSessions+1)
        random.shuffle(session_sources)
        return [os.path.join(self.config.wordList_dir % self.config.LANGUAGE,
                             '%d.txt' % sess_num)
                for sess_num in session_sources]

    def _get_session_sources(self):
        """
        Gets the filenames to be read for all sessions to be
        used for any type of experiment
        :return: the filename for each session
        """
        if self.is_stim_experiment():
            return self._get_stim_session_sources()
        else:
            return self._get_nonstim_session_sources()

    def _read_session_source(self, session_source_file):
        """
        Reads the words from a session source file into a 2D array
        :param session_source_file: the filename to be read
        :return: 2D array of words
        """
        session_lists = [x.strip().split() for x in codecs.open(session_source_file, encoding='utf-8').readlines()]

        # Check to make sure they're all the right length
        assert all([len(this_list) == self.config.listLen for this_list in session_lists])

        # Convert into TextPool items
        return [[self.wp.findBy(name=word) for word in trial] for trial in session_lists]

    def is_stim_experiment(self):
        """
        :return: Whether or not this is a stim session
        """
        stim_type = self.config.stim_type
        if stim_type == 'CLOSED_STIM':
            return True
        elif stim_type == 'NO_STIM':
            return False
        else:
            raise Exception('STIM TYPE:%s not recognized' % stim_type)

    def _prepare_single_session_lists(self, session_source_file):
        """
        Creates the lists for a single session
        :param session_source_file: File containing the lists that will be used in this session
                                    Lists should have stim lists first (if any) then nonstim
        :return:(session_lists, session_lists_is_stim)
        """
        session_source_lists = self._read_session_source(session_source_file)

        # Shuffle within the lists
        Utils.shuffle_inner_lists(session_source_lists)

        # Split the lists by type
        (stim_lists, nonstim_lists, ) = self._split_session_lists_by_stim_type(session_source_lists)

        # Shuffle within the list types so we can just pop later
        random.shuffle(stim_lists)
        random.shuffle(nonstim_lists)

        # Put the baseline trials at the front
        ordered_session_lists = []
        ordered_list_is_stim = []
        for _ in range(self.config.nBaselineTrials):
            ordered_session_lists.append(nonstim_lists.pop())
            ordered_list_is_stim.append(False)

        remaining_lists, remaining_is_stim = \
            self._shuffle_stimulation(stim_lists, nonstim_lists)

        # Put the rest of the lists shuffled at the back
        ordered_session_lists.extend(remaining_lists)
        ordered_list_is_stim.extend(remaining_is_stim)

        return ordered_session_lists, ordered_list_is_stim

    @staticmethod
    def _shuffle_stimulation(stim_lists, nonstim_lists):
        """
        pseudo-randomly assigns stim to trials such that each half of trials have an
        equal number of stim and non-stim lists
        :return: (shuffled_lists, shuffled_is_stim)
        """
        stim_halves = (0, len(stim_lists)/2, len(stim_lists))
        nonstim_halves = (0, len(nonstim_lists)/2, len(nonstim_lists))

        all_lists = []
        all_stims = []

        for i in range(2):
            half_lists = stim_lists[stim_halves[i]:stim_halves[i+1]] + \
                         nonstim_lists[nonstim_halves[i]:nonstim_halves[i+1]]
            half_stims = [True]*(stim_halves[i+1]-stim_halves[i]) + \
                         [False]*(nonstim_halves[i+1]-nonstim_halves[i])
            half_lists, half_stims = \
                Utils.shuffle_together(half_lists, half_stims)
            all_lists += half_lists
            all_stims += half_stims
        return all_lists, all_stims

    def _split_session_lists_by_stim_type(self, session_lists):
        """
        Splits lists into stim lists and nonstim lists
        NOTE: Assumes that the lists in the input are in the order:
            [*<stim_lists>, *<nonstim_lists>]
        :param session_lists: 2D matrix of size nLists x wordsPerList of all possible lists
        :return: (stim_lists, nonstim_lists)
        """
        stim_lists = session_lists[:self.config.nStimTrials]
        nonstim_lists = session_lists[self.config.nStimTrials:]
        return stim_lists, nonstim_lists

    def _prepare_practice_lists(self):
        """
        Prepares the words for the practice list
        """
        practice_words = [line.strip() for line in
                          codecs.open(self.config.practice_wordList % self.config.LANGUAGE,
                                      encoding='utf-8').readlines()]
        practice_lists = []
        for _ in range(self.config.numSessions):
            this_list = practice_words[:]
            random.shuffle(this_list)
            practice_lists.append(this_list)
        return practice_lists

    def _prepare_all_sessions_lists(self):
        """
        Prepares word lists for all sessions
        :return: (words_by_session, stim_lists_by_session)
        """
        self._assert_good_list_params()
        self._verify_files()

        words_by_session = []
        stim_lists_by_session = []

        session_sources = self._get_session_sources()

        for session_source in session_sources:
            (this_session_words, this_session_list_stim,) = \
                self._prepare_single_session_lists(session_source)
            words_by_session.append(this_session_words)
            stim_lists_by_session.append(this_session_list_stim)

        return words_by_session, stim_lists_by_session

    def _make_latex_preamble(self):
        """
        Makes the preamble for the LaTeX document
        :return: a list with the preamble
        """
        preamble = [
            '\\documentclass{article}',
            '\\usepackage[margin=1in]{geometry}',
            '\\usepackage{multirow}',
            '\\usepackage{tabularx}',
            '\\begin{document}',
            '\\begin{center}',
            '{\\large %s RAM\\_%s word lists}' %
            (self.subject.replace('_', '\\_'), self.config.EXPERIMENT_NAME),
            '\\end{center}',
            ''
        ]
        return preamble

    def make_stim_forms(self):
        """
        Generate and compile LaTeX code containing a table with each
        trial's words spread between two rows. The header of each table
        states the type of stimulation to be used in that trial.
        """
        exp = self.exp
        config = self.config
        state = exp.restoreState()
        subj = self.subject

        # Loop through sessions
        for session_i in range(config.numSessions):

            # Set the session, so the form goes in that folder
            exp.setSession(session_i)
            form_name = '%s_%s_s%d_wordlists' \
                % (subj, config.EXPERIMENT_NAME, session_i)
            stim_form = exp.session.createFile(form_name + '.tex')

            # Sets up the initial part of the LaTeX document
            preamble = self._make_latex_preamble()

            document = []

            trial_stim = state.sessionStim[session_i]
            trial_words = state.sessionLists[session_i]

            for (trial_i, (this_words, this_stim)) in enumerate(zip(trial_words, trial_stim)):

                # insert vertical space
                document.append('\\vspace{.1in}')

                # Wordlist items are centered
                centers = 'c ' * (config.listLen / 2)
                document.append('\\hspace{.5in}\\begin{tabular}{r||' + centers + '}')
                rowline1 = '\\multirow{2}{*}{List %d%s} & ' % (trial_i + 1, '' if trial_i + 1 >= 10 else '~~')
                # Word list must be an even number for this to work predictably
                for i in range(len(this_words) / 2):
                    word = this_words[i]
                    bold_word = ('\\textbf{%s}' % word.name) if this_stim else word.name
                    rowline1 += (' & ' if i != 0 else '') + bold_word.encode('utf-8')
                rowline1 += '\\\\'
                document.append(rowline1)
                rowline2 = '\\cline{2-7}\t\t\t& '
                for i in range(len(this_words) / 2, len(this_words)):
                    word = this_words[i]
                    bold_word = ('\\textbf{%s}' % word.name) if this_stim else word.name
                    rowline2 += (' & ' if i != len(this_words) / 2 else '') + bold_word.encode('utf-8')
                rowline2 += '\\\\'
                document.append(rowline2)
                document.append('\\end{tabular}')
                document.append('')

            postamble = ['\\end{document}']

            stim_form.write('\n'.join(preamble) + '\n' + '\n'.join(document) + '\n' + '\n'.join(postamble))

            stim_form.close()

            # Make the dvi document
            os.system('cd %s; latex %s >> latexLog.txt' % (os.path.dirname(stim_form.name), stim_form.name))

            # Convert the dvi to pdf
            dvi_form = exp.session.createFile(form_name + '.dvi')
            dvi_form.close()
            os.system('cd %s; dvipdf %s >> latexLog.txt' % (os.path.dirname(dvi_form.name), dvi_form.name))

            # Clean up unneccesary files
            os.system('cd %s; rm %s.dvi; rm %s.log; rm %s.aux' % (os.path.dirname(dvi_form.name),
                      form_name, form_name, form_name))

    def _show_making_stim_forms(self):
        self.video.clear('black')
        self.video.showCentered(Text('Making word list files.\nThis may take a moment...'))
        self.video.updateScreen()

    def is_session_started(self):
        """
        :return: True if this session has previously been started
        """
        state = self.exp.restoreState()
        return state.session_started

    def is_experiment_started(self):
        """
        :return: True if experiment has previously been started
        """
        state = self.exp.restoreState()
        if state:
            return True
        else:
            return False

    def _write_lst_files(self, session_lists, practice_lists):
        """
        Writes .lst files to the session folders
        :param session_lists: word lists for each list for each session
        """
        for session_i, (lists, practice_list) in enumerate(zip(session_lists, practice_lists)):
            # Set the session so it writes the files in the correct place
            self.exp.setSession(session_i)
            self._write_single_lst_file(practice_list, 'p.lst')
            for list_i, words in enumerate(lists):
                self._write_single_lst_file([word.name for word in words], '%d.lst' % list_i)

    def _write_single_lst_file(self, words, label):
        """
        Writes a single .lst file to the current session folder
        :param words: word list for that specific trial
        :param label: name of the file to be written in the session folder
        """
        list_file = self.exp.session.createFile(label)
        list_file.write('\n'.join([Utils.remove_accents(word) for word in words]))
        list_file.close()

    def init_experiment(self):
        """
        Initializes the experiment, sets up the state so that lists can be run
        :return: state object
        """

        if self.is_experiment_started():
            raise Exception('Cannot prepare trials with an in progress session!')

        Utils.seed_rng(self.exp.getOptions().get('subject'))

        self._copy_word_pool()

        # Notify the user that we're preparing the trials
        # TODO: MOVE TO VIEW
        self._show_prepare_message()

        # Make the word lists
        (session_lists, session_stim, ) = self._prepare_all_sessions_lists()
        practice_lists = self._prepare_practice_lists()

        # Write out the .lst files
        self._write_lst_files(session_lists, practice_lists)

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

        self._show_making_stim_forms()
        self.make_stim_forms()

        self.exp.setSession(0)
        return self.exp.restoreState()

    def get_stim_type(self):
        """
        Gets the type of stimulation for the given session
        :return: type of stimulation
        """
        return 'NO_RECORD' if self.config.experiment == 'FR0' else\
               'NO_STIM' if self.config.experiment == 'FR1' else\
               'OPEN_STIM' if self.config.experiment == 'FR2' else\
               'CLOSED_STIM' if self.config.experiment == 'FR3' else\
               'UNKNOWN'


class FRExperimentRunner:

    def __init__(self, fr_experiment, clock, log, mathlog, video, audio):
        self.fr_experiment = fr_experiment
        self.config = fr_experiment.config
        self.clock = clock
        self.log = log
        self.mathlog = mathlog
        self.video = video
        self.audio = audio
        self.start_beep = CustomBeep(self.config.startBeepFreq,
                               self.config.startBeepDur,
                               self.config.startBeepRiseFall)
        self.stop_beep = CustomBeep(self.config.stopBeepFreq,
                              self.config.stopBeepDur,
                              self.config.stopBeepRiseFall)
        self._on_screen = True

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
        """
        Presents "message" to user
        :return: True if user pressed Y, False if N
        """
        bc = ButtonChooser(Key('Y'), Key('N'))
        (_, button, _) = Text(message).present(bc=bc)
        return button == Key('Y')

    def _check_should_run_practice(self, state):
        """
        Checks if practice should be skipped
        :param state:
        :return:True if practice list should be run again
        """
        if state.practiceDone:
            return self.choose_yes_or_no(
                'Practice list already ran.\nPress Y to run again\nPress N to skip'
            )
        elif self.config.experiment == 'FR1':
            return self.choose_yes_or_no(
                'Would you like to run the practice list?\nPress Y to continue\nPress N to skip to first list'
            )

    def _check_sess_num(self, state):
        """
        Prompts the user to check the session number
        :return: True if verified, False otherwise
        """
        subj = self.fr_experiment.subject
        return self.choose_yes_or_no(
            'Running %s in session %d of %s\n(%s).\n Press Y to continue, N to quit' %
            (subj,
             state.sessionNum + 1,
             self.config.experiment,
             state.language))

    def _send_state_message(self, state, value):
        """
        Sends message with STATE information to control pc
        :param state: 'PRACTICE', 'ENCODING', 'WORD'...
        :param value: True/False
        """
        if state not in self.config.state_list:
            raise Exception('Improper state %s not in list of states' % state)
        self._send_event('STATE', state=state, value=value)

    def _send_trial_message(self, trial_num):
        """
        Sends message with TRIAL information to control pc
        :param trial_num: 1, 2, ...
        """
        self._send_event('TRIAL', trial=trial_num)

    def _send_event(self, type, *args, **kwargs):
        """
        Sends an arbitrary event
        :param args: Inputs to RAMControl.sendEvent()
        """
        if self.config.control_pc:
            ram_control.send(ram_control.build_message(type, *args, **kwargs))

    def _show_message_from_file(self, filename):
        """
        Opens a file with utf-8 encoding, displays the message, waits for any key
        :param filenamze: file to be read
        """
        waitForAnyKeyWithCallback(self.clock, Text(codecs.open(filename, encoding='utf-8').read()),
                                  onscreenCallback=lambda: self._send_state_message('INSTRUCT', True),
                                  offscreenCallback=lambda: self._send_state_message('INSTRUCT', False))

    def _run_practice_list(self, state):
        """
        Runs a practice list
        :param state: state object
        """
        # Retrieve the list from the state object
        practice_list = state.practiceLists[state.sessionNum]

        # Run the list
        self._send_state_message('PRACTICE', True)
        self.clock.tare()
        self.log_message('PRACTICE_TRIAL')
        self._run_list(practice_list, is_practice=True)
        self._send_state_message('PRACTICE', False)

        # Log in state that list has been run
        state.practiceDone = True
        self.fr_experiment.exp.saveState(state)

        # Show a message afterwards
        self._show_message_from_file(self.config.post_practiceList % state.LANG)

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

    def _countdown(self):
        """
        Shows the 'countdown' video, centered.
        """
        self.video.clear('black')
        self._send_state_message('COUNTDOWN', True)
        self.log_message('COUNTDOWN_START')
        self.play_whole_movie(self.config.countdownMovie)
        self._send_state_message('COUNTDOWN', False)
        self.log_message('COUNTDOWN_END')

    def _on_orient_update(self, *args):
        if self._on_screen:
            self._send_state_message('ORIENT', True)
        else:
            self._send_state_message('ORIENT', False)
            self._send_state_message(self._state_name, True)
        self._on_screen = not self._on_screen

    def _run_list(self, word_list, state=None, is_stim=False, is_practice=False):
        """
        runs a single list of the experiment, presenting all of the words
        in word_list, and logging them as <list_type>_WORD
        :param word_list: words to present
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
                self._send_trial_message(state.trialNum + 1)
                trial_label = 'trial #%d' % (state.trialNum + 1)
            else:
                self._send_trial_message(-1)
                trial_label = 'practice trial'

            timestamp = waitForAnyKeyWithCallback(self.clock,
                                                  Text('Press any key for %s' % trial_label),
                                                  onscreenCallback=lambda: self._send_state_message('WAITING', True),
                                                  offscreenCallback=lambda: self._send_state_message('WAITING', False))
        else:
            timestamp = self.clock
            if is_practice:
                self._send_trial_message(-1)

        if not is_practice:
            self.log_message('TRIAL\t%d\t%s' %
                             (state.trialNum + 1, 'STIM' if is_stim else 'NONSTIM'), timestamp)

        # Need a synchronization close to the start of the list
        self._resynchronize(False)

        # Countdown to start...

        self._countdown()

        # Display the "cross-hairs" and log

        self._state_name = 'STIM ENCODING' if is_stim else 'NON-STIM ENCODING'

        self._on_screen = True
        on_update = self._on_orient_update
        self.video.addUpdateCallback(on_update)
        cbref = self.video.update_callbacks[-1]
        timestamp_on, timestamp_off = flashStimulusWithOffscreenTimestamp(Text(self.config.orientText,
                                                                               size=self.config.wordHeight),
                                                                          clk=self.clock,
                                                                          duration=self.config.wordDuration
                                                                          )
        self.log_message('%sORIENT' % list_type, timestamp_on)
        self.log_message('%sORIENT_OFF' % list_type, timestamp_off)
        # Delay before words
        self.clock.delay(self.config.PauseBeforeWords, jitter=self.config.JitterBeforeWords)
        self.clock.wait()
        self.video.removeUpdateCallback(cbref)

        # ENCODING

        for word_i, word in enumerate(word_list[:-1]):
            self._present_word(word, word_i, is_stim, is_practice)

        # Last word has a callback so it has to be done separately
        self._present_word(word_list[-1], len(word_list)-1, is_stim, is_practice,
                           offscreen_callback=lambda *args: self._send_state_message(self._state_name, False))

        if self.config.doMathDistract and \
                not self.config.continuousDistract and \
                not self.config.fastConfig:
            self._do_distractor(is_practice)

        self._run_recall(state, is_practice)

    def _recall_orient_onscreen_callback(self, *args):
        if not self._orient_sent:
            self._send_state_message('ORIENT', True)
            self._orient_sent = True

    def _run_recall(self, state=None, is_practice=False):
        """
        Runs the recall period of a word list
        :param state: State object
        :param is_practice: True if list is practice list
        """
        self._orient_sent = False

        # Add a callback and get the reference
        update_callback = self._recall_orient_onscreen_callback
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
            self._send_state_message('ORIENT', False)

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
                                             startCallback=lambda *args: self._send_state_message('RETRIEVAL', True))

        # Ending beep
        end_timestamp = self.stop_beep.present(self.clock,
                                               onCallback=lambda *args: self._send_state_message('RETRIEVAL', False))

        # Log start and end of recall
        self.log_message('%sREC_START' % prefix, timestamp)
        self.log_message('%sREC_END' % prefix, end_timestamp)

    def _on_word_update(self, *args):
        self._send_state_message('WORD', self._on_screen)
        if self._offscreen_callback and not self._on_screen:
            self._offscreen_callback()
        self._on_screen = not self._on_screen

    def _present_word(self, word, word_i, is_stim=False, is_practice=False, offscreen_callback=None):
        """
        Presents a single word to the subject
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
                                                                    updateCallback=self._on_word_update)
        # Log that we showed the word
        ram_control.send(WordMessage(word))
        if not is_practice:
            self.log_message(u'WORD\t%s\t%s\t%d\t%s' %
                             ('text', Utils.remove_accents(word), word_i, 'STIM' if is_stim else 'NO_STIM'),
                             timestamp_on)
            self.log_message(u'WORD_OFF', timestamp_off)
        else:
            self.log_message((u'PRACTICE_WORD\t%s' % word).encode('utf-8'), timestamp_on)
            self.log_message(u'PRACTICE_WORD_OFF', timestamp_off)

        if self.config.continuousDistract:
            self._do_distractor(is_practice)

    def _do_distractor(self, is_practice=False):
        """
        Presents the subject with a single distractor period
        """

        self._send_state_message('DISTRACT', True)
        self.log_message('DISTRACT_START')

        customMathDistract(clk=self.clock,
                           mathlog=self.mathlog,
                           numVars=self.config.MATH_numVars,
                           maxProbs=self.config.MATH_maxProbs,
                           plusAndMinus=self.config.MATH_plusAndMinus,
                           minDuration=self.config.MATH_minDuration,
                           textSize=self.config.MATH_textSize)

        self._send_state_message('DISTRACT', False)
        self.log_message('DISTRACT_END')

    def should_skip_session(self, state):
        """
        Check if session should be skipped
        :return: True if session is skipped, False otherwise
        """
        if self.fr_experiment.is_session_started():
            bc = ButtonChooser(Key('SPACE') & Key('RETURN'), Key('ESCAPE'))
            self.video.clear('black')
            (_, button, timestamp) = Text(
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
                self.fr_experiment.exp.saveState(state)
                waitForAnyKey(self.clock, Text('Session skipped\nRestart RAM_%s to run next session' %
                                               self.config.experiment))
                return True
        return False

    def resync_callback(self):
        flashStimulus(Text("Syncing..."), 500)

    def _resynchronize(self, show_syncing):
        """
        Performs a resynchronization (christian's algorithm)
        (to be run before each list)
        """
        if self.config.control_pc:
            if show_syncing:
                ram_control.align_clocks(callback=self.resync_callback)
            else:
                ram_control.align_clocks()

    def _run_all_lists(self, state):
        """
        Runs all of the lists in the given session, read from state
        :param state: State object
        """
        lists = state.sessionLists[state.sessionNum]
        is_stims = state.sessionStim[state.sessionNum]
        while state.trialNum < len(lists):
            this_list = lists[state.trialNum]
            is_stim = is_stims[state.trialNum]
            self._run_list([word.name for word in this_list], state, is_stim)
            state.trialNum += 1
            self.fr_experiment.exp.saveState(state)
            self._resynchronize(True)

    def run_session(self, keyboard):
        """
        Runs a full session of free recall
        """
        config = self.config

        self._send_state_message('INSTRUCT', True)
        self.log_message('INSTRUCT_VIDEO\tON')
        playIntro.playIntro(self.fr_experiment.exp, self.video, keyboard, True, config.LANGUAGE)
        self._send_state_message('INSTRUCT', False)
        self.log_message('INSTRUCT_VIDEO\tOFF')

        # set priority
        # TODO: What does this do?
        if config.doRealtime:
            setRealtime(config.rtPeriod, config.rtComputation, config.rtConstraint)

        # Get the state object
        state = self.fr_experiment.exp.restoreState()

        # Return if out of sessions
        if self.is_out_of_sessions(state):
            return

        # Set the session appropriately for recording files
        self.fr_experiment.exp.setSession(state.sessionNum)

        # Set the default font
        setDefaultFont(Font(self.config.defaultFont))

        # Clear the screen
        self.video.clear('black')

        if not self._check_sess_num(state):
            exit(1)

        self.video.clear('black')

        stim_type = self.fr_experiment.get_stim_type()
        stim_session_type = '%s_SESSION' % stim_type
        self.log_message('SESS_START\t%s\t%s\tv_%s' % (
                         state.sessionNum + 1,
                         stim_session_type,
                         str(self.config.VERSION_NUM)))

        # Reset the list number on the control PC to 0
        self._send_trial_message(-1)
        self._send_event('SESSION', session=state.sessionNum + 1, session_type=stim_type)

        self._send_state_message('MIC TEST', True)
        self.log_message('MIC_TEST')
        if not customMicTest(2000, 1.0):
            return
        self._send_state_message('MIC TEST', False)

        if state.trialNum == 0:
            self._resynchronize(False)
            self._run_practice_list(state)
            self._resynchronize(True)
            state = self.fr_experiment.exp.restoreState()

        self._run_all_lists(state)

        self.fr_experiment.exp.saveState(state,
                                         trialNum=0,
                                         session_started=False,
                                         sessionNum=state.sessionNum+1,
                                         practiceDone=False)

        timestamp = waitForAnyKey(self.clock, Text('Thank you!\nYou have completed the session.'))
        self.log_message('SESS_END', timestamp)
        self._send_event('EXIT')

        self.clock.wait()

    @staticmethod
    def is_out_of_sessions(state):
        """
        :return: true if all sessions have been run, False otherwise
        """
        return state.sessionNum >= len(state.sessionLists)


def cleanupRAMControl():
    """
    Cleanup anything related to the Control PC
    Close connections, terminate threads.
    """


def exit(num):
    """
    Override sys.exit since Python does not exit until all threads have exited
    """
    try:
        cleanupRAMControl()
    finally:
        sys.exit(num)


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
        exit(1)

    cb = lambda: flashStimulus(Text("Waiting for start from control PC..."))
    ram_control.wait_for_start_message(poll_callback=cb)


def run():
    """
    The main function that runs the experiment
    """
    setup_logging(level=logging.DEBUG)
    checkVersion(MIN_PYEPL_VERSION)

    # Start PyEPL, parse command line options
    exp = Experiment(use_eeg=False)
    exp.parseArgs()
    exp.setup()

    # Users can quit with escape-F1
    exp.setBreak()
    RAMControl.instance().register_handler("EXIT", exit)

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

    connect_to_control_pc(subject, session + 1, config)

    fr_experiment = FRExperiment(exp, config, video, clock)

    if not fr_experiment.is_experiment_started():
        state = fr_experiment.init_experiment()
    else:
        state = exp.restoreState()

    log = LogTrack('session')
    mathlog = LogTrack('math')
    audio = CustomAudioTrack('audio')
    keyboard = KeyTrack('keyboard')

    experiment_runner = FRExperimentRunner(fr_experiment,
                                           clock,
                                           log,
                                           mathlog,
                                           video,
                                           audio,
                                           )

    if experiment_runner.should_skip_session(state):
        return

    experiment_runner.run_session(keyboard)


if __name__ == "__main__":
    run()
