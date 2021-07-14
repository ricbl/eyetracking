classdef InteractiveHighlightArrow  < InteractiveTemplate
    properties
        drawn;
        center;
        radius;
        poly_points;
        id;
        flush;
    end
        
    methods
        function s = InteractiveHighlightArrow(mainWindow, center, flush)
            s@InteractiveTemplate(Depths.image_depth,'InteractiveHighlightArrow', mainWindow, 1);
            s.drawn = 0;
            s.center = center;
            s.radius = s.mainWindow.fontSize*2;
            s.poly_points = [cos(0)*s.radius+s.center(1) sin(0)*s.radius+s.center(2); cos(5*pi/6)*s.radius+s.center(1) sin(5*pi/6)*s.radius+center(2);cos(7*pi/6)*s.radius+s.center(1) sin(7*pi/6)*s.radius+s.center(2)];
            s.id = java.util.UUID.randomUUID;
            s.flush = flush;
            s.mainWindow.structured_output.add_message('InteractiveHighlightArrow','total_cases_completed_this_session', s.mainWindow.completed_control.total_cases_completed_this_session);
            s.mainWindow.structured_output.add_message('InteractiveHighlightArrow','last_case_calibration', s.mainWindow.last_case_calibration);
        end
        
        function interaction_map = update(s)
            interaction_map = containers.Map({'changed','exit'}, {~s.drawn,ChangeScreen.No});
            s.drawn = 1;
        end
       
        function draw(s, cumulative_drawing)
            persistent last_drawn_trial;
            persistent last_drawn_id;
            if s.flush
                last_drawn_trial = [];
                last_drawn_id = [];

                s.flush = 0;
            end
            
            if ~isempty(last_drawn_trial)
                if last_drawn_id~=s.id && s.mainWindow.completed_control.total_cases_completed_this_session == last_drawn_trial
                    return;
                end
            end
            if s.mainWindow.completed_control.total_cases_completed_this_session-s.mainWindow.last_case_calibration+1>=25 %|| s.mainWindow.completed_control.total_cases_completed_this_session==0
                 cumulative_drawing.add_fill_poly(s.depth, [1 0 0],  s.poly_points,1);
                 last_drawn_trial = s.mainWindow.completed_control.total_cases_completed_this_session;
                 last_drawn_id = s.id;
            end
        end
    end
end