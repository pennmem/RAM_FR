function [ wordNos ] = wordsToNos( fname , RAM_FR_WORDS)
%wordNos = WORDSTONOS(fname, RAM_FR_WORDS)
%   Returns a vectors of the number corresponding to each element in fname
%   if wordNos(i,j)=k, then the word that appears at (i,j) in fname is
%   RAM_FR_WORDS{k}
words = textread(fname,'%s');
wordNos = nan(12,25);
for i=1:numel(words)
    wordNos(i) = find(strcmp(words{i}, RAM_FR_WORDS));

end
wordNos = wordNos';

