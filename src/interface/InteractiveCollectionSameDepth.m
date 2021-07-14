classdef InteractiveCollectionSameDepth < InteractiveTemplate
    properties
       elements;
       elements_names_index;
       middle_screen_changed_last_update;
       changed_last_update;
    end
    methods
        function s = InteractiveCollectionSameDepth(depth, name, mainWindow,elements, is_mid_screen)
            s@InteractiveTemplate(depth, name, mainWindow, is_mid_screen);
            elements_names = {};
            for ii = length(elements):-1:1
                elements_names{ii} = elements{ii}.name;
            end
            if ~isempty(elements_names)
                s.elements_names_index = containers.Map(elements_names, 1:length(elements_names));
            else
                s.elements_names_index =containers.Map();
            end
            s.elements = elements;
            s.changed_last_update = ones(1, length(s.elements));
            s.middle_screen_changed_last_update = 1;
        end
        
        function add_element(s, element, is_middle_screen)
            s.elements_names_index(element.name) = length(s.elements)+1;
            s.elements{end+1} = element;
            element.on_instantiation(s);
            s.changed_last_update(end+1) = 1;
        end
        
        function element = get_element_by_name(s,name)
            element = s.elements{s.elements_names_index(name)};
        end
        
        function apply_function_to_all(s, fn)
            for ii = 1:length(s.elements)
               fn(s.elements{ii});
            end
        end
        
        function interaction_map = before_destruction(s)
            change_screen = ChangeScreen.No;
            n_screens_to_skip = 1;
            for ii = 1:length(s.elements)
               interaction = s.elements{ii}.before_destruction;
               if interaction('exit')~=ChangeScreen.No
                   change_screen = interaction('exit');
                    if isKey(interaction,'n_screens_to_skip')
                       n_screens_to_skip = interaction('n_screens_to_skip');
                   end
               end

            end
            interaction_map = containers.Map({'exit', 'n_screens_to_skip'}, {change_screen, n_screens_to_skip});
        end
        
        function on_instantiation(s, parent)
            on_instantiation@InteractiveTemplate(s,parent);
            s.apply_function_to_all(@(element)element.on_instantiation(parent));
        end
        
        function buttons = draw(s, mouse,keyboard, cumulative_drawing)
            for ii = 1:length(s.elements)
                element = s.elements{ii};
                if s.changed_last_update(ii) || (s.middle_screen_changed_last_update && element.is_middle_screen) || cumulative_drawing.frame_to_draw_all
    %                 start_time = GetSecs;
                    element = s.elements{ii};
                    if isa(element,'InteractiveCollectionSameDepth')
                        element.draw(mouse,keyboard,cumulative_drawing);
                    else
                        element.draw(cumulative_drawing);
                    end

    %                 'draw'
    %                 class(element)
    %                end_time = start_time - GetSecs
                    mouse.update();
%                 keyboard.update();
                end
            end
        end
        
        function interaction_map = update(s, mouse, keyboard)
            changed = 0;
            s.changed_last_update = zeros(1, length(s.elements));
            s.middle_screen_changed_last_update = 0;
            exit = ChangeScreen.No;
            for ii = length(s.elements):-1:1
%                 start_time = GetSecs;
                element = s.elements{ii};
                if isa(element,'InteractiveCollectionSameDepth')
                    interaction = element.update(mouse,keyboard);
%                     mouse.update();
%                     keyboard.update();
                else
                    interaction = element.update();
                end
               if interaction('changed')
                  changed = 1; 
                  s.changed_last_update(ii) = 1;
                  if element.is_middle_screen
                      s.middle_screen_changed_last_update = 1;
                  end
               end
               if interaction('exit')~=ChangeScreen.No
                  exit = interaction('exit'); 
               end
%                'update'
%                class(element)
%                end_time = start_time - GetSecs
               mouse.update();
               
            end
            interaction_map = containers.Map({'changed', 'exit'}, {changed, exit});
        end
        
        function interaction_map = interact(s, mouse_inputs, keyboard_inputs, mouse, keyboard)
            interacted = 0;
            cursor = '';
            for ii = length(s.elements):-1:1
                
%                 start_time = GetSecs;
                element = s.elements{ii};
                if isa(element,'InteractiveCollectionSameDepth')
                    interaction = element.interact(mouse_inputs, keyboard_inputs, mouse, keyboard); 
%                     mouse.update();
%                     keyboard.update();
                else
                    interaction = element.interact(mouse_inputs, keyboard_inputs); 
                end
                if ~strcmp(interaction('cursor'),'')
                   cursor = interaction('cursor');
               end
               if interaction('interacted')
                   interacted = 1;
                   break 
               end
               
%                'interact'
%                class(element)
%                end_time = start_time - GetSecs
                mouse.update();
               
            end
            interaction_map = containers.Map({'interacted','cursor'}, {interacted, cursor});
        end
        
    end
end