classdef InteractiveCollectionSeveralDepths < InteractiveTemplate
    properties
       elements;
    end
    methods
        function s = InteractiveCollectionSeveralDepths(mainWindow, elements, depth, name, is_mid_screen)
            s@InteractiveTemplate(depth, name, mainWindow, is_mid_screen);
            s.elements = elements;
        end
        
        function add_element(s, element)
            s.elements{end+1} = element;
        end
        
        function drawable_elements_list = get_drawable_elements_list(s)
            drawable_elements_list = {};
            for ii = length(s.elements):-1:1
                drawable_elements_list{ii} = s.elements{ii};
            end
            drawable_elements_list{end+1} = s;
        end
        
    end
end