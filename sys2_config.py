# THIS FILE SETS THE CONFIGURATIONS
# FOR FR IN SYSTEM 2.0
EXPERIMENT_NAME = 'FR3'

require_labjack = False

numSessions = 10

# %s will be replaced by config.LANGUAGE
wordList_dir = 'pools_%s/stim_lists'

# Control PC options
control_pc = 1              # Will be incremented later for other control pc versions.  Set to 0 to turn off control pc processing
heartbeat = 1000            # milliseconds
syncMeasure = False         # If True, sync pulses are sent to the syncbox at the same time as a 'SYNC' messages to the Control PC
syncCount = 5               # number of sync messages before control PC is 'synced'
syncInterval = 500          # milliseconds
is_hardwire = False;         # Should be set to 'True' in production code



