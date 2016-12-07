function lists = shuffleWords(lists)
odds = [1,2,5,6,9,10];
evens = [3,4,7,8,11,12];
for l=1:length(lists)
    words = lists(l,:);
    oddWords = words(odds);
    evenWords = words(evens);
    oddWords = oddWords(randperm(length(oddWords)));
    evenWords = evenWords(randperm(length(evenWords)));
    words(odds) = oddWords;
    words(evens) = evenWords;
    lists(l,:) = words;
end