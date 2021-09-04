classdef InteractiveTemplate < handle
    properties
        trial;
        structured_output;
        parent;
        mainWindow;
        drawing_depth;
        name;
        depth;
        is_middle_screen;
    end
    methods
        function s = InteractiveTemplate(depth, name, mainWindow,is_middle_screen)
           s.depth = depth; 
           s.name = name;
           s.mainWindow = mainWindow;
           s.structured_output = mainWindow.structured_output;
           if ~exist('is_middle_screen','var')
              is_middle_screen=0;
            end
           s.is_middle_screen = is_middle_screen;
        end
        
        function on_instantiation(s, parent)
            s.parent = parent;
        end
        
        function drawable_elements_list = get_drawable_elements_list(s)
            drawable_elements_list = {s};
        end
        
        function interaction_map = before_destruction(s)
            interaction_map = containers.Map({'exit'}, {ChangeScreen.No});
        end

        function interaction_map = interact(s, mouse, keyboard)
            interaction_map = containers.Map({'interacted', 'cursor'}, {0,''});
        end

        function draw(s, cumulative_drawing)
            
        end
        
        function interaction_map = update(s)
            interaction_map = containers.Map({'changed', 'exit'}, {0, ChangeScreen.No});
        end
        
        function save_state(s, state)
            
        end
        
        function load_state(s)
            
        end
    end
end

