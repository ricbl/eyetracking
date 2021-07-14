classdef ScreenBBoxCollection < InteractiveScreen
    methods
        function s = ScreenBBoxCollection(mainWindow, certainty_list, shape, from_center, list_disease_required_box_if_selected, list_disease_forbidden_box_if_not_selected, spacing_after_buttons)
            image = InteractiveImageWithZoom(mainWindow);
            bbox_collection = BBoxCollection(mainWindow,certainty_list, image, shape, from_center, list_disease_required_box_if_selected, list_disease_forbidden_box_if_not_selected, spacing_after_buttons);
%             elements = {InteractiveScreenCapture(mainWindow, 'bbox_screen'), ButtonNext(mainWindow, 1),ButtonBack(mainWindow, -3),ButtonChooseScreen(mainWindow), InteractiveCaseScreenText(mainWindow),bbox_collection,image , ButtonResetImage(mainWindow)};
            elements = {ButtonNext(mainWindow, 1),ButtonBack(mainWindow, -3),ButtonChooseScreen(mainWindow), InteractiveCaseScreenText(mainWindow),bbox_collection,image , ButtonResetImage(mainWindow)};
            s@InteractiveScreen(mainWindow, elements)
            
                        
            state_key = [num2str(mainWindow.screen_i), '_', 'BBoxCollection'];
            if isKey(mainWindow.states,state_key)
                bbox_collection.load_state(mainWindow.states(state_key));
            end
        end
    end
end