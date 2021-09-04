classdef ButtonChoice < InteractiveCollectionSameDepth
    properties
        chosen_in_previous_update;
        single_choice;
        y_per_button;
        current_y;
        rect;
        initial_rect;
        has_none_of_the_above;
        can_skip;
        chosen_string;
        save_labels;
        chosen_index;
        chosen_single_in_previous_update;
        require_at_least_one_choice;
        hidden;
        chosen;
        choices;
        default_choices;
        canHoldClicked;
        spacing_after;
        spacing;
    end
    methods
        function s = ButtonChoice(mainWindow,choices,name,rect, single_choice, has_none_of_the_above, can_skip, save_labels, require_at_least_one_choice, default_choices, canHoldClicked, spacing_after)
            
           s@InteractiveCollectionSameDepth(Depths.button_depth,strcat('ButtonChoice','_',name),mainWindow, {}, 0);
           if length(single_choice)==1
                single_choice = ones(1,length(choices))*single_choice;
           end
           if ~exist('spacing_after','var')
                s.spacing_after = zeros( 1,length(choices) );
           else
               s.spacing_after = spacing_after;
           end
           s.require_at_least_one_choice = require_at_least_one_choice;
           s.has_none_of_the_above = has_none_of_the_above;
           s.can_skip = can_skip;
           s.save_labels = save_labels;
           s.chosen_string = '';
           s.chosen_index = None();
           s.y_per_button = rect(4)-rect(2);
           s.spacing = ceil(s.y_per_button*0.2);
           s.current_y = rect(2);
           s.rect = rect;
           s.initial_rect = rect;
           s.choices = {};
           if ~exist('canHoldClicked','var')
                s.canHoldClicked = 1;
           else
               s.canHoldClicked = canHoldClicked;
           end
           for i=1:length(choices)
               s.add_button(choices{i}, single_choice(i))
           end
           s.chosen_in_previous_update = zeros( 1,length(choices) );
           s.chosen_single_in_previous_update = zeros( 1,length(choices) );
           s.single_choice = single_choice;
           s.hidden = 0;
           if ~exist('default_choices','var')
                s.default_choices = zeros( 1,length(s.elements) );
           else
               s.default_choices = default_choices;
           end
          
           s.reset_chosen();
        end
        
        function state = save_state(s)
            state = containers.Map();
            state('chosen') = s.chosen;
%             state('chosen_string') = s.chosen_string;
%             state('chosen_index') = s.chosen_index;
        end
        
        function load_state(s, state)
            s.set_chosen(state('chosen'));
%             s.chosen = state('chosen');
%             s.chosen_string = state('chosen_string');
%             s.chosen_index = state('chosen_index');
        end
        
        function add_button(s, text, single_choice)
            s.choices{end+1} = text;
            if s.current_y + 2*s.y_per_button > s.mainWindow.screenRect(4)
               s.current_y = s.rect(2);
               delta_x = s.rect(3)-s.rect(1) + 10;
               s.rect(1) = s.rect(1) + delta_x;
               s.rect(3) = s.rect(3) + delta_x;
            end
            s.add_element(MyButton(text, [s.rect(1) s.current_y s.rect(3) s.current_y+s.y_per_button], s.canHoldClicked, strcat(class(s),'_',s.name,'_',text), s.mainWindow));
            s.current_y = s.current_y + s.y_per_button;
            if length(s.spacing_after)>=length(s.elements)
                if s.spacing_after(length(s.elements))
                    s.current_y = s.current_y + s.spacing;
                end
            end
            s.chosen_in_previous_update = zeros( 1,length(s.chosen_in_previous_update)+1 );
            s.chosen_single_in_previous_update = zeros( 1,length(s.chosen_in_previous_update)+1 );
            s.single_choice(end+1) = single_choice;
            s.default_choices(end+1) = 0;
        end
        
        function choices = get_choices(s)
            choices = s.choices;
        end
        
        function update_chosen(s)
            chosen = [];
            for ii = length(s.elements):-1:1
                chosen(ii) = s.elements{ii}.get_clicked;
            end
            s.chosen = chosen;
        end
        
        function chosen = get_chosen(s)
            chosen = s.chosen;
        end
        
        function set_chosen(s, chosen)
            for ii = length(s.elements):-1:1
                if chosen(ii)
                    s.elements{ii}.set_clicked();
                else
                    s.elements{ii}.set_active();
                end
            end
        end
        
        function reset_chosen(s)
            s.set_chosen(s.default_choices);
        end
        
        function interaction_map = interact(s, mouse_input,keyboard_input,mouse,keyboard)
            interaction_map = containers.Map({'interacted', 'cursor'}, {0,''});
            if ~s.hidden
                if ~None.isNone(mouse_input('mouse_change_x'))
                    interaction_map = interact@InteractiveCollectionSameDepth(s, mouse_input,keyboard_input,mouse,keyboard);
                end
            end
        end
        
        function interaction_map = update(s, mouse,keyboard)
            s.update_chosen();
            chosen = s.get_chosen();
            if s.require_at_least_one_choice
                if sum(chosen)==0 
                    s.parent.get_element_by_name('ButtonNext').set_inactive;
                else
                    s.parent.get_element_by_name('ButtonNext').unset_inactive;
                end
            end
            
            interaction = update@InteractiveCollectionSameDepth(s,mouse,keyboard);
            changed = interaction('changed');
            exit = interaction('exit');
            if ~isequal(chosen, s.chosen_in_previous_update)
                changed = 1;
                if sum(s.single_choice)>0
                    if sum(s.chosen_single_in_previous_update)>0
                        s.elements{find(s.chosen_single_in_previous_update)}.set_active();
                        chosen(find(s.chosen_single_in_previous_update)) = 0;
                    end
                    chosen_single = s.single_choice .* chosen;
                    if sum(chosen_single)>0
                        if sum(s.chosen_in_previous_update)>0
                            cellfun(@(c)c.set_active(),s.elements(logical(s.chosen_in_previous_update)));
                            chosen(logical(s.chosen_in_previous_update)) = 0;
                        end
                        s.chosen_index = find(chosen_single);
                        s.chosen_string = s.elements{s.chosen_index}.text;
                    else
                        s.chosen_index = None();
                        s.chosen_string = '';
                    end
                    s.chosen_single_in_previous_update = chosen_single;
                end
            end

            s.chosen_in_previous_update = chosen;
            interaction_map = containers.Map({'changed', 'exit'}, {changed, exit});
        end
        
        function unhide(s)
            s.hidden = 0;
            s.apply_function_to_all(@(element)element.unhide());
        end
        
        function hide(s)
            s.hidden = 1;
            s.apply_function_to_all(@(element)element.hide());
        end
        
               
       function attach_function_clicked(s, fn)
            s.apply_function_to_all(@(element)element.attach_function_clicked(fn));
       end
        
        function unset_inactive(s)
            s.apply_function_to_all(@(element)element.unset_inactive());
        end
        
        function set_inactive(s)
            s.apply_function_to_all(@(element)element.set_inactive());
        end
        
        function interaction_map = before_destruction(s)
            s.update_chosen();
            s.mainWindow.states([num2str(s.mainWindow.screen_i), '_', s.name]) = s.save_state;
            n_screens_to_skip = 2;
            interaction = before_destruction@InteractiveCollectionSameDepth(s);
            if interaction('exit')~=ChangeScreen.No
                interaction_map = interaction;
                return;
            end
            exit = ChangeScreen.No;
            if s.save_labels
                s.structured_output.add_message(s.name,'chosen_label', s.chosen_string);
                s.structured_output.add_message(s.name,'chosen_index', s.chosen_index);
                chosen = s.get_chosen();
                choices = s.get_choices();
                for i=1:length(chosen)
                    s.structured_output.add_message(s.name,choices{i},chosen(i));
                end

                if s.can_skip
                    if ~any(cell2mat(chosen))
                        exit = ChangeScreen.SkipScreens;
                    end
                end

                s.mainWindow.add_labels(s.name,containers.Map({'labels','chosen','single_choice'},{choices,chosen, s.single_choice}));
            end
            interaction_map = containers.Map({'exit','n_screens_to_skip'}, {exit,n_screens_to_skip});
        end
    end
end