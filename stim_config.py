# RAM_FR configuration for STIM SESSIONS ONLY.
# Other configuration in the main config file

EXPERIMENT_NAME = 'FR2'

# THIS IS HOW THE REST OF THE PROGRAM KNOWS THIS IS A STIM SESSION
do_stim = True

numSessions = 10

# %s will be replaced by config.LANGUAGE
wordList_dir = 'pools_%s/stim_lists'

# MS pre-stimulus that stimulation should be on for
prestimulus_stim = 200

nStimLocs = 1
# How long to send stim pulse
stim_pulseFrequency = 50  # Hz
stim_nPulses        = 230 # (Corresponds to 4.6 seconds)
stim_burstFrequency = 0   # NO BURSTING
stim_nBursts        = 0   # NO BURSTING
stim_pulseDuration  = 300 # uS



