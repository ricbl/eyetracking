classdef InteractiveWarning  < InteractiveTemplate
    properties
        drawn;
        center;
        radius;
        poly_points;
        id;
        flush;
        ratio_bad_data;
        longest_blink;
    end
        
    methods
        function s = InteractiveWarning(mainWindow)
            s@InteractiveTemplate(Depths.box_depth,'InteractiveWarning', mainWindow, 1);
            edffile = s.mainWindow.et.part_1_edffile;
%                  edffile = '../../experiments/test_204_20210301-173835-9614/et1.EDF';
%                  edffile = ['../../anonymized_collected_data/user1_et/et', num2str(s.mainWindow.current_trial), '.EDF'];
%                 edffile = '../../experiments/user3_204_20210311-101017-9152/et39.EDF';
            trim_file = [edffile,'_warning.txt'];
            if ~isfile(trim_file)
                first_time = 1;
                script_name = 'run_check_eytracking_quality.sh';
                [~, ~] = jsystem(['../scripts/',script_name,' --file_name ',edffile]);  
            else
                first_time=0;
            end
            trim_start = splitlines(fileread([edffile,'_warning.txt']));
            s.ratio_bad_data = str2num(trim_start{1});
            s.longest_blink = str2num(trim_start{2});
            distance_from_nearest_fixation_to_next_screen_button = 0;%str2num(trim_start{3});
            if distance_from_nearest_fixation_to_next_screen_button>=0
                s.mainWindow.drift_check.add_distance_button(distance_from_nearest_fixation_to_next_screen_button, s.mainWindow.current_trial);
            end
            s.mainWindow.structured_output.add_message('InteractiveWarning','ratio_bad_data', s.ratio_bad_data);
            s.mainWindow.structured_output.add_message('InteractiveWarning','longest_blink', s.longest_blink);
            s.mainWindow.structured_output.add_message('InteractiveWarning','distance_from_nearest_fixation_to_next_screen_button', distance_from_nearest_fixation_to_next_screen_button);
            if first_time
                if s.ratio_bad_data>=0.15 | s.longest_blink>=3000
                   s.mainWindow.completed_control.case_not_completed; 
                else
                   s.mainWindow.completed_control.case_completed; 
                end
            end
            
        end
        
        function interaction_map = update(s)
            interaction_map = containers.Map({'changed','exit'}, {~s.drawn,ChangeScreen.No});
            
        end
       
        function draw(s, cumulative_drawing)  
%             if ~s.drawn
%                 edffile = s.mainWindow.et.part_1_edffile;
%                 if ~isfile(edffile)
%                 trim_start = splitlines(fileread([edffile,'_warning.txt']));
% %                  edffile = '../../experiments/test_204_20210301-173835-9614/et1.EDF';
% %                  edffile = ['../../anonymized_collected_data/phase_2/user2_et/et', num2str(s.mainWindow.current_trial), '.EDF'];
% %                 edffile = '../../experiments/user3_204_20210311-101017-9152/et39.EDF';
%                 script_name = 'run_check_eytracking_quality.sh';
%                 edffile
%                 [~, ~] = jsystem(['../scripts/',script_name,' --file_name ',edffile]);  
%                 trim_start = splitlines(fileread([edffile,'_warning.txt']));
%                 s.ratio_bad_data = str2num(trim_start{1});
%                 s.longest_blink = str2num(trim_start{2});
%                 distance_from_nearest_fixation_to_next_screen_button = 0;%str2num(trim_start{3});
%                 if distance_from_nearest_fixation_to_next_screen_button>=0
%                     s.mainWindow.drift_check.add_distance_button(distance_from_nearest_fixation_to_next_screen_button, s.mainWindow.current_trial);
%                 end
%                 s.mainWindow.structured_output.add_message('InteractiveWarning','ratio_bad_data', s.ratio_bad_data);
%                 s.mainWindow.structured_output.add_message('InteractiveWarning','longest_blink', s.longest_blink);
%                 s.mainWindow.structured_output.add_message('InteractiveWarning','distance_from_nearest_fixation_to_next_screen_button', distance_from_nearest_fixation_to_next_screen_button);
%                 if s.ratio_bad_data>=0.15 | s.longest_blink>=3000
%                    s.mainWindow.completed_control.case_not_completed; 
%                 end
%             end
            if s.mainWindow.drift_check.get_moving_average()>85
                cumulative_drawing.add_formatted_text(s.depth, ['Warning Level 2: average drift = ', num2str(s.mainWindow.drift_check.get_moving_average()),' pixels'] , 'center', (s.mainWindow.screenRect(4)+s.mainWindow.screenRect(2))/2+s.mainWindow.fontSize*24, [1 0 0]);
            end
            if s.ratio_bad_data>=0.15
                cumulative_drawing.add_formatted_text(s.depth,  ['Warning Level 2: missing data = ', num2str(s.ratio_bad_data*100),'%'] , 'center', (s.mainWindow.screenRect(4)+s.mainWindow.screenRect(2))/2+s.mainWindow.fontSize*20, [1 0 0]);
            elseif s.ratio_bad_data>=0.1
                 cumulative_drawing.add_formatted_text(s.depth, ['Warning Level 1: missing data = ', num2str(s.ratio_bad_data*100),'%'] , 'center', (s.mainWindow.screenRect(4)+s.mainWindow.screenRect(2))/2+s.mainWindow.fontSize*20, [1 1 0]);
            end
            if s.longest_blink>=3000
                cumulative_drawing.add_formatted_text(s.depth, ['Warning Level 2: long period of missing data = ', num2str(s.longest_blink/1000.), 's'] , 'center', (s.mainWindow.screenRect(4)+s.mainWindow.screenRect(2))/2+s.mainWindow.fontSize*22, [1 0 0]);
            elseif s.longest_blink>=1500
                cumulative_drawing.add_formatted_text(s.depth, ['Warning Level 1: long period of missing data = ', num2str(s.longest_blink/1000.), 's'] , 'center', (s.mainWindow.screenRect(4)+s.mainWindow.screenRect(2))/2+s.mainWindow.fontSize*22, [1 1 0]);
            end
            
            s.drawn = 1;
        end
    end
end