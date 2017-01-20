# THIS FILE SETS THE CONFIGURATIONS
# FOR FR IN SYSTEM 2.0

# ALL SYSTEM2.0 CONFIGURATION OPTIONS
experiment = 'FR3'
stim_type = 'CLOSED_STIM'
version = '3.0'
control_pc = True
heartbeat_interval = 1000

state_list = [ 
    'PRACTICE',
    'STIM ENCODING',
    'NON-STIM ENCODING',
    'RETRIEVAL',
    'DISTRACT',
    'INSTRUCT',
    'COUNTDOWN',
    'WAITING',
    'WORD',
    'ORIENT',
    'MIC TEST',
 ]

require_labjack = False

do_stim = True

numSessions = 10

nStimTrials = 11
nBaselineTrials = 3
nControlTrials = 11

# %s will be replaced by config.LANGUAGE
wordList_dir = 'pools_%s/stim_lists'
