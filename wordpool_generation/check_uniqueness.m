function [ max_inCommon ] = check_uniqueness( sets )
%CHECK_UNIQUENESS Summary of this function goes here
%   Detailed explanation goes here
max_inCommon  = zeros(length(sets),25);
for i=1:length(sets)
    s1 = sets{i};
    for j=1:25
        this_list = s1(j,:);
        for k=1:length(sets)
            if k==i
                continue
            end
            s2 = sets{k};
            for l=1:25
                other_list = s2(l,:);
                max_inCommon(i,j) = max([max_inCommon(i,j),sum(ismember(this_list, other_list))]);
            end
        end
    end
end
        

end
