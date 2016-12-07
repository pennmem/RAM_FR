function [ was_vals, wordNos] = make_n_sessions(n, WAS, percentile)
%[was_vals, wordNos] = MAKE_N_SESSIONS(n, WAS, percentile)
% makes a set of n sessions worth of lists in which items are chosen 
% such that the pairwise
% WAS value (or LSA) is chosen from the top percentile
% each was_val is the pairwise WAS value between that item and the rest of
% the list.
was_vals = nan(n,25);
wordNos = cell(n,1);
for i=1:n
[was_vals(i,:), wordNos{i}] = makeLists(WAS, percentile);
end

