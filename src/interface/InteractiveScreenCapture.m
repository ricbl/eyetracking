classdef InteractiveScreenCapture < InteractiveTemplate
    properties
        file_suffix;
    end
    methods
        function s = InteractiveScreenCapture(mainWindow, file_suffix)
           s@InteractiveTemplate(Depths.ScreenCaptureDepth, 'InteractiveScreenCapture',mainWindow, 1);
           s.file_suffix = file_suffix;
        end
        
        function interaction_map = before_destruction(s)
            image_object = s.parent.get_element_by_name('InteractiveImage');
            image_object.reset();
            
            s.parent.update(None(), None());
            s.parent.middle_screen_changed_last_update = 1;
            Screen('FillRect', s.mainWindow.winMain, [0 0 0], [s.mainWindow.margin 0 s.mainWindow.screenRect(3)-s.mainWindow.screenRect(1)-s.mainWindow.margin s.mainWindow.screenRect(4)-s.mainWindow.screenRect(2)]);
            
            s.parent.draw(None(),None(),s.parent.cumulative_drawing);
            s.parent.cumulative_drawing.reset();
            
            screenImageArray = Screen('GetImage', s.mainWindow.winMain,[], 'backBuffer');
            Screen('Flip', s.mainWindow.winMain);
            Screen('FillRect', s.mainWindow.winMain, [0 0 0 0]);
            Screen('Flip', s.mainWindow.winMain);
            imwrite(screenImageArray, [s.structured_output.local, '/',s.file_suffix,'_',num2str(s.structured_output.current_trial) '.png']);
            interaction_map = containers.Map({'exit'}, {ChangeScreen.No});
        end
    end
    
end