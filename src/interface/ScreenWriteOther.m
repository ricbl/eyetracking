classdef ScreenWriteOther < InteractiveScreen
    methods
        function s = ScreenWriteOther(mainWindow)
            question = @(mainWindow)['Write what the other findings were, separating them with a ";" or a new line.'];
            %input_obj = InteractiveInputText(mainWindow,mainWindow.margin+10, mainWindow.get_center_y - mainWindow.screenRect(2), question, 'center', mainWindow.get_center_y-mainWindow.screenRect(2)-150);
            input_obj = TextBox(mainWindow,[mainWindow.margin+10, mainWindow.get_center_y - mainWindow.screenRect(2)-(mainWindow.screenRect(4)-mainWindow.screenRect(2))*0.3+(ceil(length(question(mainWindow))*mainWindow.character_width/(mainWindow.screenRect(3)-mainWindow.screenRect(1)-2*mainWindow.margin))*mainWindow.fontSize)*1.2, mainWindow.screenRect(3)-mainWindow.margin-10-mainWindow.screenRect(1), 0 ],'');
            instructions = InteractiveGenericText(mainWindow, question, mainWindow.margin+10, mainWindow.get_center_y - mainWindow.screenRect(2)-(mainWindow.screenRect(4)-mainWindow.screenRect(2))*0.3, floor((mainWindow.screenRect(3)-mainWindow.screenRect(1) - 2*mainWindow.margin-20)/mainWindow.character_width));
            
            button_next = ButtonNextWriteOther(mainWindow);
            
            
            button_reset = ButtonResetImage(mainWindow, 'TextBox', 'Reset Text');
%             elements = {ButtonBack(mainWindow), ButtonChooseScreen(mainWindow),button_next, input_obj, button_reset, instructions, InteractiveCaseScreenText(mainWindow)};
            elements = {button_next, input_obj, button_reset, instructions, InteractiveCaseScreenText(mainWindow)};
            s@InteractiveScreen(mainWindow, elements);
            
            state_key = [num2str(mainWindow.screen_i), '_', 'TextBox'];
            if isKey(mainWindow.states,state_key)
                input_obj.load_state(mainWindow.states(state_key));
            end
        end
    end
end