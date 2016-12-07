function [ allLists_WAS, allWordNos] = make_counterbalanced_list( WAS , WAS_percentile, set1)
%[allLists_WAS, allWordNos] = MAKE_COUNTERBALANCED_LIST(WAS, WAS_percentile, set1)
% Makes a single counterbalanced list (based on set1). Odd words on first
% list will be even words on set2. In addition, pairwise WAS_percentile is
% kept above the specified value.

% Evens and odd words
onBlocks = [1,2,5,6,9,10];
offBlocks = [3,4,7,8,11,12];
% Even and odd lists
onLists = 1:2:25;
offLists = 2:2:25;

% Gotta get the "on" words and "off" words
set1OnOn = set1(onLists, onBlocks);
set1OffOff = set1(offLists, offBlocks);
onWords = [set1OnOn(:); set1OffOff(:)];
set1OnOff = set1(onLists, offBlocks);
set1OffOn = set1(offLists, onBlocks);
offWords = [set1OnOff(:); set1OffOn(:)];

% get WordNos, Remove allNaN wordNos
wordNos = 1:length(WAS);
allNan_wordNos = wordNos(all(isnan(WAS)));
wordNos(all(isnan(WAS))) = [];

% mean pairwise WAS for each list
allLists_WAS = nan(1,25);
% WordNos that haven't been used yet
wordNosLeft = wordNos;

% The actual wordNos used
allWordNos = nan(25 ,12);

% (for diagnostics)
usedOff= 0;
usedOn = 0;
checkerboard = nan(25,12);

% Loop through the 25 lists
for i=1:25
    % Words for this list
    this_wordNos = nan(1,12);
    
    % Get usable wordNos based on set1. (also diagnostics)
    if xor(any(i==onLists),any(1==onBlocks))
        usable_wordNosLeft = offWords(ismember(offWords, wordNosLeft));
        checkerboard(i,1) = 1;
        usedOff = usedOff +1;
    else
        usable_wordNosLeft = onWords(ismember(onWords, wordNosLeft));
        checkerboard(i,1) = 0;
        usedOn = usedOn+1;
    end
    
    % Get random word to start with
    this_wordNos(1) = usable_wordNosLeft(randsample(length(usable_wordNosLeft),1));
    wordNosLeft(wordNosLeft == this_wordNos(1)) = [];
    
    % Loop until second-to-last word
    for j=2:11
        used_wordNos = this_wordNos(~isnan(this_wordNos));
        % Again, get wordNosLeft that are stim/nostim
        if xor(any(i==onLists),any(j==onBlocks))
            checkerboard(i,j) = 1;
            usedOff = usedOff+1;
            usable_wordNosLeft = offWords(ismember(offWords, wordNosLeft));
        else
            checkerboard(i,j) = 0;
            usedOn = usedOn+1;
            usable_wordNosLeft = onWords(ismember(onWords, wordNosLeft));
        end
        try
            % Get mean pairwise WAS between used and remaining
            meanWAS = nanmean(WAS(used_wordNos, wordNos(ismember(wordNos,usable_wordNosLeft))),1);
            % Get a top word
            good_wordNosLeft = usable_wordNosLeft(meanWAS>=prctile(meanWAS, WAS_percentile));
            this_wordNos(j) = good_wordNosLeft(randsample(length(good_wordNosLeft),1));
            wordNosLeft(wordNosLeft==this_wordNos(j)) = [];
        catch e
            % Shouldn't happen
            disp([i,j]);
            throw(e)
        end
    end
    % Get remaining wordNos
    if xor(any(i==onLists),any(12==onBlocks))
        usable_wordNosLeft = offWords(ismember(offWords, allNan_wordNos));
        usedOff = usedOff +1;
    else
        usable_wordNosLeft = onWords(ismember(onWords, allNan_wordNos));
        usedOn = usedOn+1;
    end
    % Last word comes from allNan words
    this_wordNos(12) = usable_wordNosLeft(randsample(length(usable_wordNosLeft),1));
    allNan_wordNos(allNan_wordNos == this_wordNos(12)) = [];
    this_was = WAS(this_wordNos, this_wordNos);
    allLists_WAS(i) = nanmean(nanmean(this_was));
    allWordNos(i,:) = this_wordNos;
end