classdef ButtonSkipImage < MyButton
    properties
        skip_count;
        
    end
    methods
        function s = ButtonSkipImage(mainWindow, skip_count)
            s@MyButton('Skip: non-diagnostic quality',ButtonSkipImage.get_rect(mainWindow), 0, 'ButtonSkipImage', mainWindow);
            s.skip_count = skip_count;
            s.attach_function_clicked(@(a)set_to_skip(a));
        end
    end
    
    methods(Static)
        function rect = get_rect(mainWindow)
            centerY = (mainWindow.screenRect(2)+mainWindow.screenRect(4))/2;
            rect = [10 round(centerY-20*mainWindow.fontSize/21+mainWindow.screenRect(2)+30*mainWindow.fontSize/21+20*mainWindow.fontSize/21) mainWindow.margin-10 round(centerY+20*mainWindow.fontSize/21+mainWindow.screenRect(2)+30*mainWindow.fontSize/21+20*mainWindow.fontSize/21)];
        end
    end
end

function set_to_skip(s)
    if s.skip_count
        s.mainWindow.completed_control.case_not_completed;
    end
    s.structured_output.add_message('ButtonSkipImage', 'skip_image');
    s.exit_return = ChangeScreen.NextTrial;
end