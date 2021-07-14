classdef ScreenTranscriptionEditing < InteractiveScreen
    methods
        function s = ScreenTranscriptionEditing(mainWindow)
            question = @(mainWindow)['You may do minor editing to the transcription of the report:'];
            [transcript,trim_start] = mainWindow.get_live_transcription_results;
            
            input_obj = TextBox(mainWindow,[mainWindow.margin+10, mainWindow.get_center_y - mainWindow.screenRect(2)-(mainWindow.screenRect(4)-mainWindow.screenRect(2))*0.3+(ceil(length(question(mainWindow))*mainWindow.character_width/(mainWindow.screenRect(3)-mainWindow.screenRect(1)-2*mainWindow.margin))*mainWindow.fontSize)*1.2, mainWindow.screenRect(3)-mainWindow.margin-10-mainWindow.screenRect(1), 0 ],transcript);
            instructions = InteractiveGenericText(mainWindow, question, mainWindow.margin+10, mainWindow.get_center_y - mainWindow.screenRect(2)-(mainWindow.screenRect(4)-mainWindow.screenRect(2))*0.3, floor((mainWindow.screenRect(3)-mainWindow.screenRect(1) - 2*mainWindow.margin-20)/mainWindow.character_width));
            
            button_next = ButtonNext(mainWindow, 0);
            button_reset = ButtonResetImage(mainWindow, 'TextBox', 'Reset Text');
            elements = {button_next, ButtonBack(mainWindow), ButtonChooseScreen(mainWindow), input_obj, button_reset, instructions, InteractiveCaseScreenText(mainWindow)};
            s@InteractiveScreen(mainWindow, elements);
            mainWindow.structured_output.add_message('ScreenTranscriptionEditing','trim_start', trim_start);
            
            state_key = [num2str(mainWindow.screen_i), '_', 'TextBox'];
            if isKey(mainWindow.states,state_key)
                input_obj.load_state(mainWindow.states(state_key));
            end
            
        end
    end
end