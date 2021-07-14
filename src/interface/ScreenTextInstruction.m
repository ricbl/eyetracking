classdef ScreenTextInstruction < InteractiveScreen
    methods
        function s = ScreenTextInstruction(mainWindow, text_fn)
            elements = {ButtonNextBigInvisible(mainWindow), InteractiveGenericText(mainWindow,text_fn)};
            s@InteractiveScreen(mainWindow, elements);
        end
    end
end