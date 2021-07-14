classdef DriftCheck < handle
    properties
        list_distances;
        list_added_trials;
    end
    methods
        function s = DriftCheck()
            s.reset_drift;
        end
        
        function add_distance_button(s, new_distance, current_trial)
            if ~ismember(current_trial, s.list_added_trials)
                s.list_added_trials = [s.list_added_trials current_trial];
                s.list_distances = [s.list_distances new_distance];
            end
        end
        
        function moving_average = get_moving_average(s)
            if length(s.list_distances)>=4
                moving_average = mean(s.list_distances(end-3:end));
            else
               moving_average = 0; 
            end
        end
        
        function reset_drift(s)
            s.list_distances = [];
        end
    end
end