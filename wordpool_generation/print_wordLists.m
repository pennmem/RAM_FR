function  print_wordLists( wordNos, words , prefix)
%PRINT_WORDLISTS Summary of this function goes here
%   Detailed explanation goes here
mkdir(sprintf('%sWordLists',prefix));
for i=1:length(wordNos)
    this_wordNos = wordNos{i};
    this_words = words(this_wordNos);
    fid = fopen(sprintf('%sWordLists/%d.txt',prefix,i),'w');
    for list_i =1:25
        this_wordlist = this_words(list_i,:);
        for word_i = 1:12
            fprintf(fid,'%s ',this_wordlist{word_i});
        end
        if list_i~=25
            fprintf(fid,'\n');
        end
    end

end

