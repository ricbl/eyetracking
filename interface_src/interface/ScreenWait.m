classdef ScreenWait < InteractiveScreen
    methods
        function s = ScreenWait(mainWindow)
            wait_obj = InteractiveWait(mainWindow);
            elements = {wait_obj, ButtonSkipTranscription(mainWindow)};
            s@InteractiveScreen(mainWindow, elements);
        end
    end
end