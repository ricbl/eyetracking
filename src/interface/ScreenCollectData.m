classdef ScreenCollectData < InteractiveScreen
    methods
        function s = ScreenCollectData(mainWindow, elements)
            elements = [ {ButtonNext(mainWindow,0)}, elements ];
            s@InteractiveScreen(mainWindow, elements)
        end
    end
end