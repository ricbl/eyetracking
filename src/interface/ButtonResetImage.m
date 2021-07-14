classdef ButtonResetImage < MyButton
    methods
        function s = ButtonResetImage(mainWindow, name_class_to_reset, text_button)
            if ~exist('name_class_to_reset','var')
                name_class_to_reset = 'InteractiveImage';
            end
            if ~exist('text_button','var')
                text_button = 'Reset Image';
            end
            s@MyButton(text_button,ButtonResetImage.get_rect(mainWindow), 0, 'ButtonResetImage', mainWindow);
            s.attach_function_clicked(@(a)reset_image(a, name_class_to_reset))
        end
    end
    
    methods(Static)
        function rect = get_rect(mainWindow)
            centerY = (mainWindow.screenRect(2)+mainWindow.screenRect(4))/2;
            rect = [10 round(centerY-20*mainWindow.fontSize/21-mainWindow.screenRect(2)-30*mainWindow.fontSize/21-20*mainWindow.fontSize/21) mainWindow.margin-10 round(centerY+20*mainWindow.fontSize/21-mainWindow.screenRect(2)-30*mainWindow.fontSize/21-20*mainWindow.fontSize/21)];
        end
    end
end

function reset_image(s, name_class_to_reset)
    s.parent.get_element_by_name(name_class_to_reset).reset;
end
