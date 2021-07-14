classdef InteractiveCaseScreenText  < InteractiveGenericText
    methods
        function s = InteractiveCaseScreenText(mainWindow)
            s@InteractiveGenericText(mainWindow, @(mainWindow)get_case_screen_string(mainWindow), 20, mainWindow.screenRect(4)-mainWindow.screenRect(2), 50);
        end
    end
end

function string_to_return = get_case_screen_string(mainWindow)
    string_to_return = [' Case ',num2str(mainWindow.current_trial),' Screen ',num2str(mainWindow.screen_i)];
    if ismember(mainWindow.screen_i,mainWindow.main_window_screens_to_choose)
        index_screen_title = mainWindow.main_window_screens_to_choose == mainWindow.screen_i;
        screen_title = mainWindow.main_window_strings_choose_screen{index_screen_title};
        string_to_return = [string_to_return, ' ', screen_title];
    end
end
            