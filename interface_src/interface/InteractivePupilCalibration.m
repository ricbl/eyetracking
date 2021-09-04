classdef InteractivePupilCalibration  < InteractiveTemplate
    properties
       et;
       time_calibration;  
       start_time;
       go_back;
    end
    methods
        function s = InteractivePupilCalibration(mainWindow, time_calibration, go_back)
            s@InteractiveTemplate(Depths.pupil_depth, 'InteractivePupilCalibration', mainWindow, 1);
            s.time_calibration = time_calibration;
            s.et = mainWindow.et;
            s.start_time = GetSecs;
            s.go_back = go_back;
        end
        
        function interaction_map = update(s)
            exit = ChangeScreen.No;
            if GetSecs()-s.start_time>s.time_calibration
                exit = ChangeScreen.NextScreen;
            end
            interaction_map = containers.Map({'changed','exit'}, {0,exit}); 
        end
        
        function draw(s, cumulative_drawing)
            cumulative_drawing.add_fill_rect(s.depth, [0.25 0.25 0.25], []);
            cumulative_drawing.add_formatted_text(s.depth, '+', 'center', 'center', [1 1 1]);
        end
        
        function on_instantiation(s, parent)
            on_instantiation@InteractiveTemplate(s,parent);
            s.et.start_recording(class(s));
            s.structured_output.add_message(class(s),'begin_pupil_calibration');
        end
        
        function interaction_map = before_destruction(s)
            s.structured_output.add_message(class(s),'end_pupil_calibration');
            s.et.end_recording(class(s));
            if s.go_back
                interaction_map = containers.Map({'exit','n_screens_to_skip'}, {ChangeScreen.SkipScreens, -2});
            else
                interaction_map = containers.Map({'exit'}, {ChangeScreen.No});
            end
        end
    end
end