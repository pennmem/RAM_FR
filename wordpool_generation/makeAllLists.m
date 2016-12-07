function makeAllLists(RAM_FR_WORDS, FR_LSA_matrix, LSA_percentile, ...
    nStim, nNonStim,...
    stimFolder, nonStimFolder)
% Makes a set of lists for RAM_FR

%% LOAD PRE-EXISTING LISTS
existing_stim_files = dir(stimFolder);
existing_stim_lists = {};
for i=1:length(existing_stim_files)
    thisFile = existing_stim_files(i).name;
    if strcmp(thisFile(1),'.')
        continue
    end
    existing_stim_lists{end+1} = wordsToNos(fullfile(stimFolder, thisFile), RAM_FR_WORDS);
end

if mod(length(existing_stim_lists),2)~=0 || mod(nStim,2) ~=0
    error('I don''t know what to do when stimLists aren''t even ')
end

%% MAKE STIM LISTS
initLists = 200;
% Make a set of 200 initial stim lists so we have some to choose from
[was_vals, wordNos] = make_n_sessions(initLists, FR_LSA_matrix, LSA_percentile);
newLists = cell(initLists,1);
newLists_WAS = cell(initLists,1);
for i=1:initLists
    if mod(i,20)==0
        fprintf('.');
    end
    try
        [newList_WAS, newList_Nos] = make_counterbalanced_list(...
            FR_LSA_matrix, LSA_percentile, wordNos{i});
        newLists{i} = newList_Nos;
        newLists_WAS{i} = newList_WAS;
    catch e
        newLists_WAS{i} = 0;
        % Not sure why this would happen...
    end
end

% Get the mean WAS values
allNewWAS = cellfun(@mean, newLists_WAS);
% include the original WAS values generated
allNewWAS = mean([allNewWAS, mean(was_vals,2)], 2);
disp(mean(allNewWAS))
% Get the best mean WAS values to put in lists
[~, I] = sort(allNewWAS);
newStimLists = cell(0);
for i=1:(nStim-length(existing_stim_lists))/2
    newStimLists{end+1} = shuffleLists(shuffleWords(wordNos{I(end-i+1)}));
    newStimLists{end+1} = shuffleLists(shuffleWords(newLists{I(end-i+1)}));
end
allStimLists = {existing_stim_lists{:}, newStimLists{:}};
disp(check_uniqueness(allStimLists));
print_wordLists(allStimLists, RAM_FR_WORDS, 'stim')


%% LOAD PRE-EXISTING LISTS (nonstim)
existing_nonstim_files = dir(nonStimFolder);
existing_nonstim_lists = {};
for i=1:length(existing_nonstim_files)
    thisFile = existing_nonstim_files(i).name;
    if strcmp(thisFile,'.') || strcmp(thisFile, '..')
        continue
    end
    existing_nonstim_lists{end+1} = wordsToNos(fullfile(nonStimFolder, thisFile), RAM_FR_WORDS);
end

if mod(length(existing_nonstim_lists),2)~=0 || mod(nStim,2) ~=0
    error('I don''t know what to do when stimLists aren''t even ')
end


% Get the best mean WAS values to put in lists
newNonStimLists = cell(0);
for i=1:(nNonStim-length(existing_nonstim_lists))/2
    newNonStimLists{end+1} = shuffleLists(shuffleWords(wordNos{I(end-i-nStim)}));
    newNonStimLists{end+1} = shuffleLists(shuffleWords(newLists{I(end-i-nStim)}));
end
allNonStimLists = {existing_nonstim_lists{:}, newNonStimLists{:}};
disp(check_uniqueness(allNonStimLists));
print_wordLists(allNonStimLists, RAM_FR_WORDS, 'nonstim')