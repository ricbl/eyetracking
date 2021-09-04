classdef ScreenSeg < InteractiveScreen
    methods
        function s = ScreenSeg(mainWindow)
            image = InteractiveImageWithZoom(mainWindow);
            bbox_collection = SegmentManager(mainWindow,image);
            elements = {InteractiveCaseScreenText(mainWindow),bbox_collection,image , ButtonResetImage(mainWindow)};
            s@InteractiveScreen(mainWindow, elements);
        end
    end
end