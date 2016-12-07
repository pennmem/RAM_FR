function [ lists ] = shuffleLists( lists )
%SHUFFLELISTS Summary of this function goes here
%   Detailed explanation goes here
odds = 1:2:25;
evens = 2:2:25;
oddLists = lists(odds,:);
evenLists = lists(evens,:);
oddLists = oddLists(randperm(size(oddLists,1)),:);
evenLists = evenLists(randperm(size(evenLists,1)),:);
lists(odds,:) = oddLists;
lists(evens,:) = evenLists;
end

