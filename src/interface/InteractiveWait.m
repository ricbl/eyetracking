classdef InteractiveWait  < InteractiveTemplate
    properties
        text;
        timer_dots;
        dot_to_erase;
        time_between_dots_in_days;
        dots_strings;
        exit_return;
        draw_first;
    end
    methods
        function s = InteractiveWait(mainWindow)
            s@InteractiveTemplate(Depths.text_depth,'InteractiveWait', mainWindow, 1);
            s.time_between_dots_in_days = 0.15/24/60/60;
            s.dot_to_erase = 1;
            s.timer_dots = now;
            s.dots_strings = {'.. ', '. .', ' ..'};
            s.exit_return = ChangeScreen.No;
            s.draw_first = 1;
            if s.mainWindow.live_transcription_active && s.mainWindow.check_live_transcription_status>0
                s.draw_first = 0;
            end
        end
        
        function interaction_map = update(s)
            if ~s.mainWindow.live_transcription_active
                s.exit_return = ChangeScreen.SkipScreens;
                 interaction_map = containers.Map({'changed','exit','n_screens_to_skip'}, {0,ChangeScreen.SkipScreens,2});
                 return;
            end
            time_now = now;
            exit = ChangeScreen.No;
            if s.mainWindow.check_live_transcription_status>0
                s.exit_return = ChangeScreen.NextScreen;
                exit = ChangeScreen.NextScreen;
            end
            changed = 0;
            if time_now - s.timer_dots > s.time_between_dots_in_days
                s.timer_dots = time_now;
                s.dot_to_erase = mod(s.dot_to_erase+1,3)+1;
                changed = 1;
            end
            interaction_map = containers.Map({'changed','exit'}, {changed,exit});
        end
        
        function interaction = before_destruction(s)
           interaction = containers.Map({'exit','n_screens_to_skip'}, {s.exit_return,2});
        end
       
        function draw(s, cumulative_drawing)
            if s.draw_first
                string_to_write = ['Waiting for transcription calculation to end', s.dots_strings{s.dot_to_erase}];
                x_pos = (s.mainWindow.screenRect(3)-s.mainWindow.screenRect(1))/2 - length(string_to_write)*s.mainWindow.character_width/2;
                cumulative_drawing.add_formatted_text(s.depth,string_to_write, x_pos, 'center', [1 1 1], 50);
            end
        end
    end
end