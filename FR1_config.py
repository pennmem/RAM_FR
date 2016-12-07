# RAM_FR configuration for NONSTIM SESSIONS ONLY.
# Other configuration in the main config file

# ALL SYSTEM2.0 CONFIGURATION OPTIONS
sys2 = {\
        'EXPERIMENT_NAME'  : 'FR1',
        'STIM_TYPE'        : 'NO_STIM',
        'VERSION_NUM'      : '2.04',
        'control_pc'       : 1,              # Will be incremented later for other control pc versions.  Set to 0 to turn off control pc processing
        'heartbeat'        : 1000,            # milliseconds
        'syncMeasure'      : False,         # If True, sync pulses are sent to the syncbox at the same time as a 'SYNC' messages to the Control PC
        'syncCount'        : 5,              # number of sync messages before control PC is 'synced'
        'syncInterval'     : 500,          # milliseconds
        'is_hardwire'      : True,         # Should be set to 'True' in production code
        'state_list' : [
                        'PRACTICE',
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
        }

require_labjack = False

# THIS IS HOW THE REST OF THE PROGRAM KNOWS THIS IS A NONSTIM SESSION
do_stim = False

numSessions = 18

nBaselineTrials = 0
nStimTrials = 0
nControlTrials = 25

# %s WILL BE REPLACED BY config.LANGUAGE
wordList_dir = 'pools_%s/nonstim_lists'
