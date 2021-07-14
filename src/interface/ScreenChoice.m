classdef ScreenChoice < InteractiveScreen
    methods
        function s = ScreenChoice(mainWindow,choices,name, single_choice, has_none_of_the_above, can_skip, include_image, require_at_least_one_choice, spacing_after_buttons) 
            y_per_button = round(45*mainWindow.fontSize/21);
            centerY = mainWindow.get_center_y();
            topY = centerY - length(choices)/2*y_per_button;
            if include_image
                centerX = mainWindow.screenRect(3)-160;
                rect = [mainWindow.screenRect(3)-(mainWindow.margin-10)-mainWindow.screenRect(1) topY-mainWindow.screenRect(2) mainWindow.screenRect(3)-10-mainWindow.screenRect(1) topY-mainWindow.screenRect(2)+y_per_button];
            else
                centerX = mainWindow.get_center_x();
                rect = [centerX-mainWindow.margin/2-mainWindow.screenRect(1) topY-mainWindow.screenRect(2) centerX+mainWindow.margin/2-mainWindow.screenRect(1) topY-mainWindow.screenRect(2)+y_per_button];
            end
            default_choices = zeros(1, length(choices) );
            default_choices(1) = 1;
            multichoice_button = ButtonChoice(mainWindow,choices,name,rect, single_choice, has_none_of_the_above, can_skip, 1, require_at_least_one_choice, default_choices, 1, spacing_after_buttons);
            elements = { ButtonNextOther(mainWindow, single_choice),InteractiveCaseScreenText(mainWindow),ButtonResetImage(mainWindow),multichoice_button};
            if include_image
                elements{end+1} = InteractiveImageWithZoom(mainWindow);
            end
            s@InteractiveScreen(mainWindow, elements);
            
            state_key = [num2str(mainWindow.screen_i), '_', 'ButtonChoice','_',name];
            if isKey(mainWindow.states,state_key)
                multichoice_button.load_state(mainWindow.states(state_key));
            end
        end
    end
end