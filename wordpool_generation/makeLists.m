function [ allLists_WAS, allWordNos] = makeLists( WAS , WAS_percentile)
%allLists_WAS, allWordNos = MAKELISTS(WAS, WAS_percentile)
%   Makes lists in which the items are chosen such that the pairwise WAS
%   value is within the top "WAS_percentile" of options

% Get wordNos from WAS, eliminate those that have only NaNs
wordNos = 1:length(WAS);
allNan_wordNos = wordNos(all(isnan(WAS)));
wordNos(all(isnan(WAS))) = [];

% Holds the mean pairwise WAS values for each list
allLists_WAS = nan(1,25);
% Start with all words
wordNosLeft = wordNos;
% Placed words
allWordNos = nan(25 ,12);
for i=1:25
    % Words for this list
    this_wordNos = nan(1,12);
    % Grab the first word randomly
    this_wordNos(1) = randsample(wordNosLeft,1);
    % remove it from the remaining words
    wordNosLeft(wordNosLeft == this_wordNos(1)) = [];
    for j=2:11
        % get the words used so far
        used_wordNos = this_wordNos(~isnan(this_wordNos));
        % mean pairwise WAS between words used so far and all remaining
        % words
        meanWAS = nanmean(WAS(used_wordNos, wordNos(ismember(wordNos,wordNosLeft))),1);
        % get the top portion of words
        good_wordNosLeft = wordNosLeft(meanWAS>=prctile(meanWAS, WAS_percentile));
        % Get a word randomly, remove from wordNosLeft
        this_wordNos(j) = good_wordNosLeft(randsample(length(good_wordNosLeft),1));
        wordNosLeft(wordNosLeft==this_wordNos(j)) = [];
    end
    % Place the last word from one of the allNaNs
    this_wordNos(12) = allNan_wordNos(randsample(length(allNan_wordNos),1));
    allNan_wordNos(allNan_wordNos == this_wordNos(12)) = [];
    % Pairwise WAS 
    this_was = WAS(this_wordNos, this_wordNos);
    allLists_WAS(i) = nanmean(nanmean(this_was));
    allWordNos(i,:) = this_wordNos;
end