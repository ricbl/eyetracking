classdef ScreenChestBox < InteractiveScreen
    methods
        function s = ScreenChestBox(mainWindow) 
            button_next = ButtonNext(mainWindow, 1);
            image = InteractiveImage(mainWindow);
%             image = InteractiveImageWithZoom(mainWindow);
            bbox = BBox(mainWindow,0,1, image, ShapesBBox.Rectangle, None());
%             bbox = Segment(mainWindow,0,1, image, None());
%             elements = {button_next,image, InteractiveScreenCapture(mainWindow, 'chest_screen'), ButtonBack(mainWindow), ButtonChooseScreen(mainWindow), ButtonResetImage(mainWindow), InteractiveCaseScreenText(mainWindow), bbox};
            elements = {button_next,image,ButtonBack(mainWindow), ButtonChooseScreen(mainWindow), ButtonResetImage(mainWindow), InteractiveCaseScreenText(mainWindow), bbox};
            s@InteractiveScreen(mainWindow, elements);
            
            state_key = [num2str(mainWindow.screen_i), '_', 'BBox_0'];
            if isKey(mainWindow.states,state_key)
                bbox.load_state(mainWindow.states(state_key));
            end
        end
        

    end
end

