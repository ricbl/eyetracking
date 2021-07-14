classdef BBoxList < InteractiveCollectionSameDepth
    properties
       box_being_edited;
       texture_middle_screen;
       box_being_edited_previous_update;
    end
    methods
        function s = BBoxList(depth, name, mainWindow,elements, texture_middle_screen)
            s@InteractiveCollectionSameDepth(depth, name, mainWindow, elements, 1);
            s.box_being_edited=None();
             s.box_being_edited_previous_update = None();
            s.texture_middle_screen = texture_middle_screen;
        end
        
        function add_element(s, element)
            add_element@InteractiveCollectionSameDepth(s, element);
        end
        
        function interaction_map = interact(s, mouse_input,keyboard_input, mouse,keyboard)
            interaction_map = containers.Map({'interacted', 'cursor'}, {0,''});
            if ~None.isNone(s.box_being_edited)
                interaction_map = s.elements{s.box_being_edited}.interact(mouse_input,keyboard_input);
            end
        end
        
        function draw(s, mouse, keyboard, cumulative_drawing)
            if s.texture_middle_screen.texture_changed_last_update
                s.texture_middle_screen.reset_texture();
            end
            draw@InteractiveCollectionSameDepth(s,mouse,keyboard, cumulative_drawing);
           [texture_width, texture_height] = Screen('WindowSize',s.texture_middle_screen.texture_index);
            cumulative_drawing.add_texture(s.depth, s.texture_middle_screen.texture_index, [], [s.mainWindow.margin 0 s.mainWindow.margin+texture_width texture_height]); 
            s.texture_middle_screen.texture_changed_last_update = 0;
        end
        
        function interaction_map = update(s, mouse,keyboard)
            changed = 0;
            if ~None.isNone(s.box_being_edited)
                interaction = s.elements{s.box_being_edited}.update();
                if interaction('changed')
                    changed = 1;
                end
            end
            if ~None.isNone(s.box_being_edited_previous_update) && ~isequal(s.box_being_edited_previous_update, s.box_being_edited)
                interaction = s.elements{s.box_being_edited_previous_update}.update();
                if interaction('changed')
                    changed = 1;
                end
            end
            s.box_being_edited_previous_update = s.box_being_edited;
            interaction_map = containers.Map({'changed', 'exit'}, {changed, ChangeScreen.No});
        end
        
    end
end