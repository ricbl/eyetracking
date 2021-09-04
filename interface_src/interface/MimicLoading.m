classdef MimicLoading  < MimicSampleLoading
    properties
        filenames;
    end
    methods   
        function s = MimicLoading(numTrials, structured_output, list_name)
            s@MimicSampleLoading(numTrials, structured_output);
            s.filenames = readtable(list_name,'ReadVariableNames',false);
        end
        function filepath = get_file_path(s,index)
            file_location = join(s.filenames(index,:).Variables,'/');
            filepath = ['../../datasets/mimic/', file_location{1}];
        end
    end
end