classdef BBoxCollection < InteractiveCollectionSeveralDepths
    properties
        boxes;
        disease_choices;
        chosen_disease;
        sum_chosen_disease_previous;
        sum_chosen_certainty_previous;
        max_boxes;
        box_chosen_index_previous_update;
        save_location_y;
        button_disease;
        button_save;
        centerY;
        button_boxes;
        button_discard;
        button_delete;
        state;
        state_previous;
        box_being_edited_state_previous_update;
        button_certainty;
        classBBox;
        associated_image;
        shape_bbox;
        chosen_diseases_in_box;
        list_disease_required_box_if_selected;
        list_disease_forbidden_box_if_not_selected;
        indices_chosen_disease;
        text_textures_box_labels;
        text_texture_title_list;
        text_texture_title_button_list;
        text_textures_diseases;
        color_not_selected;
        color_selected;
        color_past_box;
        texture_middle_screen;
        changed;
        text_texture_title_button_list_drawn;
        width_texture_text;
        labels_disease_buttons;
        text_textures_certainty_labels;
        indices_certainty_chosen_disease;
        button_change_shape;
        initial_shape_bbox;
        box_being_edited_shape_box_previous_update;
        button_advance;
        button_advance_state_previous;
    end
    
    methods
        
        function s = BBoxCollection(mainWindow, certainty_choices, associated_image, shape_bbox, from_center, list_disease_required_box_if_selected, list_disease_forbidden_box_if_not_selected, spacing_after_buttons)
            s@InteractiveCollectionSeveralDepths(mainWindow, {}, Depths.text_depth, 'BBoxCollection', 0);
            s.color_not_selected = [0.3 0.3 0.3 1.25];
            s.color_selected = [1 0.7 1 1.25];
            s.color_past_box = [0 1 0 1.25];
            s.changed = 1;
            s.text_texture_title_button_list_drawn = 0;
            s.centerY = (mainWindow.screenRect(2)+mainWindow.screenRect(4))/2;
            s.texture_middle_screen = BBoxTexture(s.mainWindow);
            
            s.associated_image = associated_image;
            s.list_disease_required_box_if_selected = list_disease_required_box_if_selected;
            s.list_disease_forbidden_box_if_not_selected = list_disease_forbidden_box_if_not_selected;
            s.shape_bbox = shape_bbox;
            s.initial_shape_bbox = shape_bbox;
            s.box_being_edited_shape_box_previous_update = shape_bbox;
            if from_center
                s.classBBox = @(varargin)BBoxFromCenter(varargin{:});
            else
                s.classBBox = @(varargin)BBox(varargin{:});
            end
            
            s.boxes = BBoxList(Depths.box_depth, 'boxes',mainWindow,{}, s.texture_middle_screen);
            s.add_element(s.boxes);
            s.max_boxes = 75;
            s.text_textures_box_labels = {};
            s.text_textures_certainty_labels = {};
            for text_label_certainty = {'9','7','5','3','1'}
                s.text_textures_certainty_labels{end+1} = Screen('MakeTexture',s.mainWindow.winMain,zeros(s.mainWindow.fontSize, s.mainWindow.character_width,4));
                Screen('TextFont',s.text_textures_certainty_labels{end},s.mainWindow.fontName);
                Screen('TextSize',s.text_textures_certainty_labels{end},floor(0.8*s.mainWindow.fontSize));
                DrawFormattedText(s.text_textures_certainty_labels{end}, text_label_certainty{1}, 'center', 'center', s.color_past_box);
            end      
            choices_chosen = s.mainWindow.get_labels('ButtonChoice_disease');
            
            s.disease_choices = choices_chosen('labels');
            s.chosen_disease = choices_chosen('chosen');
            
            single_choice = choices_chosen('single_choice');
            s.disease_choices = s.disease_choices(logical(1-single_choice));
            s.chosen_disease = s.chosen_disease(logical(1-single_choice));
            s.chosen_diseases_in_box=zeros(1,length(s.chosen_disease));
            
            s.save_location_y = round(0.78*(s.mainWindow.screenRect(4)-s.mainWindow.screenRect(2)));
            s.labels_disease_buttons = s.disease_choices;
            for i = 1:length(s.disease_choices)
                if ~s.list_disease_required_box_if_selected(i)
                    s.labels_disease_buttons{i} = strcat('(',s.labels_disease_buttons{i},')');
                end
            end
            s.button_disease = ButtonChoice(mainWindow,s.labels_disease_buttons,'button_disease',[mainWindow.screenRect(3)-(mainWindow.margin-10)-mainWindow.screenRect(1) round(15*s.mainWindow.fontSize/21) mainWindow.screenRect(3)-10-mainWindow.screenRect(1) round((s.save_location_y-30*s.mainWindow.fontSize/21-45*s.mainWindow.fontSize/21-15*s.mainWindow.fontSize/21)/(length(s.disease_choices)+length(certainty_choices))+15*s.mainWindow.fontSize/21)],0,0,0,0,0, zeros( 1,length(s.labels_disease_buttons) ), 1,spacing_after_buttons(2:end));
            for i = find(list_disease_forbidden_box_if_not_selected & ~s.chosen_disease)
                s.button_disease.elements{i}.set_inactive();
            end
            [s.indices_chosen_disease{1:length(s.disease_choices)}] = deal([]);
            [s.indices_certainty_chosen_disease{1:length(s.disease_choices)}] = deal([]);
            
            s.add_element(s.button_disease);
            s.text_textures_diseases = {};
            s.width_texture_text = {};
            for i = length(s.labels_disease_buttons):-1:1
                font_multiplier = min([s.mainWindow.margin*0.9/length(s.labels_disease_buttons{i})/s.mainWindow.character_width,0.9]);
                s.width_texture_text{i} = length(s.labels_disease_buttons{i})*floor(s.mainWindow.character_width*font_multiplier);
                s.text_textures_diseases{i} = Screen('MakeTexture', s.mainWindow.winMain, zeros(s.mainWindow.fontSize, s.width_texture_text{i}), 4);
                Screen('TextFont',s.text_textures_diseases{i},s.mainWindow.fontName);
                Screen('TextSize',s.text_textures_diseases{i},floor(floor(s.mainWindow.character_width*font_multiplier)/s.mainWindow.character_width*s.mainWindow.fontSize));
                if s.chosen_disease(i)
                    color = s.color_selected;
                else
                    color = s.color_not_selected;
                end
                DrawFormattedText(s.text_textures_diseases{i}, s.labels_disease_buttons{i}, 'center', 'center', color);
            end
            
            s.text_texture_title_list = Screen('MakeTexture', s.mainWindow.winMain, zeros(s.mainWindow.fontSize, 22*s.mainWindow.character_width, 4));
            Screen('TextFont',s.text_texture_title_list,s.mainWindow.fontName);
            Screen('TextSize',s.text_texture_title_list,s.mainWindow.fontSize);
            Screen('BlendFunction', s.text_texture_title_list, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
            nx = DrawFormattedText(s.text_texture_title_list, 'Labels ',0, 'center', [1 1 1 1.25]);
            nx = DrawFormattedText(s.text_texture_title_list, 'selected',nx, 'center', s.color_selected);
            DrawFormattedText(s.text_texture_title_list, '-',nx, s.mainWindow.fontSize*0.75, [1 1 1 1.25]);
            DrawFormattedText(s.text_texture_title_list, 'Box ID',nx+s.mainWindow.character_width,'center', s.color_past_box);
            
            s.text_texture_title_button_list = Screen('MakeTexture', s.mainWindow.winMain, zeros(s.mainWindow.fontSize*2, 17*s.mainWindow.character_width, 4));
            Screen('TextFont',s.text_texture_title_button_list,s.mainWindow.fontName);
            Screen('TextSize',s.text_texture_title_button_list,s.mainWindow.fontSize);
            Screen('BlendFunction', s.text_texture_title_button_list, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
            DrawFormattedText(s.text_texture_title_button_list, 'Select past boxes\nto modify them:','center','center', [1 1 1 1.25]);
            
            s.button_certainty = ButtonChoice(mainWindow,certainty_choices,'button_certainty',[mainWindow.screenRect(3)-(mainWindow.margin-10)-mainWindow.screenRect(1) round(15+(s.save_location_y-30*s.mainWindow.fontSize/21-45*s.mainWindow.fontSize/21-15*s.mainWindow.fontSize/21)/(length(s.disease_choices)+length(certainty_choices))*length(s.disease_choices)+15*s.mainWindow.fontSize/21+2*s.mainWindow.fontSize) mainWindow.screenRect(3)-10-mainWindow.screenRect(1) round((s.save_location_y-30*s.mainWindow.fontSize/21-45*s.mainWindow.fontSize/21)/(length(s.disease_choices)+length(certainty_choices))+15*s.mainWindow.fontSize/21+(s.save_location_y-30*s.mainWindow.fontSize/21-45*s.mainWindow.fontSize/21-15*s.mainWindow.fontSize/21)/(length(s.disease_choices)+length(certainty_choices))*length(s.disease_choices)+15*s.mainWindow.fontSize/21+2*s.mainWindow.fontSize) ],1,0,0,0, 0, [1 0 0 0 0]);
            s.add_element(s.button_certainty);
            
            s.button_change_shape = MyButton('Change BBox Shape',[mainWindow.screenRect(3)-(mainWindow.margin-10)-mainWindow.screenRect(1) round(s.save_location_y-30*s.mainWindow.fontSize/21) mainWindow.screenRect(3)-10-mainWindow.screenRect(1) round(s.save_location_y+10*s.mainWindow.fontSize/21)],0,'save_button',mainWindow); 
            s.button_change_shape.attach_function_clicked(@(a)when_change_clicked(a,s));
            %s.add_element(s.button_change_shape);
            
            s.button_save = MyButton('Save New Box',[mainWindow.screenRect(3)-(mainWindow.margin-10)-mainWindow.screenRect(1) round(s.save_location_y-30*s.mainWindow.fontSize/21+50*s.mainWindow.fontSize/21) mainWindow.screenRect(3)-10-mainWindow.screenRect(1) round(s.save_location_y+10*s.mainWindow.fontSize/21+50*s.mainWindow.fontSize/21)],0,'save_button',mainWindow); 
            s.button_save.attach_function_clicked(@(a)when_save_clicked(a,s));
            s.add_element(s.button_save);
            
            s.button_boxes = ButtonChoice(mainWindow, {},'button_boxes',[10 round(s.centerY+90*s.mainWindow.fontSize/21-s.mainWindow.screenRect(2)+3*s.mainWindow.fontSize+160*mainWindow.fontSize/21) round(1.1*mainWindow.fontSize+10) round(s.centerY+90*s.mainWindow.fontSize/21-s.mainWindow.screenRect(2)+4*s.mainWindow.fontSize+160*mainWindow.fontSize/21)], 1, 0,0,0, 0 );
            s.add_element(s.button_boxes);
            s.button_discard = MyButton('Cancel Changes',[mainWindow.screenRect(3)-(mainWindow.margin-10)-mainWindow.screenRect(1) round(s.save_location_y-30*s.mainWindow.fontSize/21+100*s.mainWindow.fontSize/21) mainWindow.screenRect(3)-10-mainWindow.screenRect(1) round(s.save_location_y+10*s.mainWindow.fontSize/21+100*s.mainWindow.fontSize/21)],0,'button_discard',mainWindow); 
            s.button_discard.attach_function_clicked(@(a)when_discard_clicked(a,s));
            s.add_element(s.button_discard);
            s.button_delete = MyButton('Delete Box',[mainWindow.screenRect(3)-(mainWindow.margin-10)-mainWindow.screenRect(1) round(s.save_location_y-30*s.mainWindow.fontSize/21+150*s.mainWindow.fontSize/21) mainWindow.screenRect(3)-10-mainWindow.screenRect(1) round(s.save_location_y+10*s.mainWindow.fontSize/21+150*s.mainWindow.fontSize/21)], 0, 'button_delete', mainWindow); 
            s.button_delete.attach_function_clicked(@(a)when_delete_clicked(a,s));
            s.add_element(s.button_delete);
            
            s.button_advance = MyButton('All Required Labels Were Selected',[mainWindow.screenRect(3)-(mainWindow.margin-10)-mainWindow.screenRect(1) round(s.save_location_y-30*s.mainWindow.fontSize/21+200*s.mainWindow.fontSize/21) mainWindow.screenRect(3)-10-mainWindow.screenRect(1) round(s.save_location_y+10*s.mainWindow.fontSize/21+200*s.mainWindow.fontSize/21)], 1, 'button_advance', mainWindow); 
            s.add_element(s.button_advance);
            s.button_advance_state_previous  = StatesMyButton.Active;
            
            s.state = StatesBBoxCollection.NotEditing;
            s.boxes.box_being_edited = None();
            s.box_being_edited_state_previous_update = StatesBBox.Discarded;
            s.set_own_buttons_not_editing;
            s.state_previous = s.state;
        end
        
        function state = save_state(s)
            state = containers.Map();
            state('n_boxes') = 0;
            for ii = 1:length(s.boxes.elements)
                if ~None.isNone(s.boxes.elements{ii}.saved_rect)
                    state(s.boxes.elements{ii}.name) = s.boxes.elements{ii}.save_state;
                    state('n_boxes') = ii;
                end
            end
            
        end
        
        function load_state(s, state)
            for ii = 1:state('n_boxes')
                s.start_new_box;
                this_box_state = state(s.boxes.elements{s.boxes.box_being_edited}.name);
                s.boxes.elements{s.boxes.box_being_edited}.load_state(this_box_state);
                when_save_clicked(None(), s, 1);
                if this_box_state('state')==StatesBBox.Deleted
                    when_delete_clicked(None(), s);
                end
            end
            s.start_new_box;
        end
        
        function interaction = before_destruction(s)
            s.mainWindow.states([num2str(s.mainWindow.screen_i), '_', s.name]) = s.save_state;
            interaction = before_destruction@InteractiveCollectionSeveralDepths(s); 
            for i = 1:length(s.text_textures_box_labels)
               Screen('Close', s.text_textures_box_labels{i}); 
            end
            
            for i = 1:length(s.text_textures_certainty_labels)
               Screen('Close', s.text_textures_certainty_labels{i}); 
            end
            
            
            Screen('Close',s.text_texture_title_list);
            Screen('Close', s.text_texture_title_button_list);
            Screen('Close',s.texture_middle_screen.texture_index);
            for i = 1:length(s.text_textures_diseases)
               Screen('Close', s.text_textures_diseases{i}); 
            end
        
            delta_total = 0;
            if None.isNone(s.boxes.elements{end}.saved_rect)
                delta_total = 1;
            end
            s.structured_output.add_message(class(s),'total_boxes', length(s.boxes.elements)-delta_total);
        end    
        
        function set_own_buttons_not_editing(s)
            s.button_save.hide();
            s.button_discard.hide();
            s.button_delete.hide();
            s.button_disease.hide();
            s.button_certainty.hide();
            s.button_change_shape.hide();
        end
        
        function return_value = check_disease_criterias_met(s)
            return_value = 1;
            if s.button_advance.get_clicked
                return;
            end
            if sum(s.list_disease_required_box_if_selected & s.chosen_disease & ~s.chosen_diseases_in_box)>0
               return_value = 0;
            end
        end
        
        function interaction = update(s)
            interaction = update@InteractiveCollectionSeveralDepths(s);
            changed = 0;
            box_chosen_index = s.button_boxes.chosen_index;
            if ~isequal(box_chosen_index,s.box_chosen_index_previous_update)
               changed = 1;
               s.when_boxchoice_clicked;
            end
            s.box_chosen_index_previous_update = box_chosen_index;
            if ~None.isNone(s.boxes.box_being_edited)
                if s.boxes.elements{s.boxes.box_being_edited}.shape_box~=s.box_being_edited_shape_box_previous_update
                    changed = 1;
                end
                if s.boxes.elements{s.boxes.box_being_edited}.state~=s.box_being_edited_state_previous_update
                    switch(s.state)
                        case {StatesBBoxCollection.NotEditing}
                            if s.boxes.elements{s.boxes.box_being_edited}.state~=StatesBBox.Discarded
                                changed = 1;
                                if None.isNone(s.boxes.elements{s.boxes.box_being_edited}.saved_rect)
                                   s.state = StatesBBoxCollection.EditingNew;
                                else
                                    s.state = StatesBBoxCollection.EditingPast;
                                end
                            end
                        case {StatesBBoxCollection.EditingNew}
                            if s.boxes.elements{s.boxes.box_being_edited}.state==StatesBBox.Discarded
                                changed = 1;
                               s.state = StatesBBoxCollection.NotEditing;
                            end
                    end    
                end
                s.box_being_edited_state_previous_update = s.boxes.elements{s.boxes.box_being_edited}.state;
                s.box_being_edited_shape_box_previous_update = s.boxes.elements{s.boxes.box_being_edited}.shape_box;
            end
            
            if s.button_advance.state~=s.button_advance_state_previous
               changed = 1; 
            end
            s.button_advance_state_previous = s.button_advance.state;
            
            if s.state~=s.state_previous
               changed = 1; 
            end
            sum_chosen_disease = sum(s.button_disease.get_chosen);
            if (sum_chosen_disease==0)~=(s.sum_chosen_disease_previous==0)
                changed = 1;
            end
            sum_chosen_certainty = sum(s.button_certainty.get_chosen);
            if (sum_chosen_certainty==0)~=(s.sum_chosen_certainty_previous==0)
                changed = 1;
            end
            if changed
                switch(s.state)
                    case {StatesBBoxCollection.NotEditing}
                        if s.check_disease_criterias_met
                            s.parent.get_element_by_name('ButtonNext').unset_inactive();
                            s.parent.get_element_by_name('ButtonBack').unset_inactive();
                        else
                            s.parent.get_element_by_name('ButtonNext').set_inactive();
                            s.parent.get_element_by_name('ButtonBack').set_inactive();
                        end
                        s.set_own_buttons_not_editing;
                    case StatesBBoxCollection.EditingNew
                        s.parent.get_element_by_name('ButtonNext').set_inactive();
                        s.parent.get_element_by_name('ButtonBack').set_inactive();
                        s.button_disease.unhide();
                        s.button_certainty.unhide();
                        s.button_change_shape.unhide();
                        s.button_save.unhide();
                        if sum_chosen_disease>0 && sum_chosen_certainty>0
                            s.button_save.unset_inactive();
                        else
                            s.button_save.set_inactive();
                        end
                        s.button_discard.hide();
                        s.button_delete.hide();
                    case StatesBBoxCollection.EditingPast

                        s.parent.get_element_by_name('ButtonNext').set_inactive();
                        s.parent.get_element_by_name('ButtonBack').set_inactive();
                        s.button_disease.unhide();
                        s.button_certainty.unhide();
                        s.button_change_shape.unhide();
                        s.button_save.unhide();
                        if s.boxes.elements{s.boxes.box_being_edited}.state==StatesBBox.Discarded
                            s.button_save.set_inactive();
                        else
                            if sum_chosen_disease>0 && sum_chosen_certainty>0
                                s.button_save.unset_inactive();
                            else
                                s.button_save.set_inactive();
                            end
                        end
                        s.button_discard.unhide();
                        s.button_delete.unhide();
                end
            end
            s.sum_chosen_disease_previous = sum_chosen_disease;
            s.sum_chosen_certainty_previous = sum_chosen_certainty;
            interaction = containers.Map({'changed', 'exit'}, { s.changed, ChangeScreen.No});
            s.changed = 0;
        end
        
        function start_new_box(s)
            n_boxes = length(s.boxes.elements);
            if isempty(s.boxes.elements) || ~None.isNone(s.boxes.elements{end}.saved_rect)
                if n_boxes<s.max_boxes
                    s.boxes.add_element(s.classBBox(s.mainWindow, n_boxes+1, 0, s.associated_image, s.shape_bbox, s.texture_middle_screen));
                    n_boxes = n_boxes + 1;
                    s.text_textures_box_labels{end+1} = Screen('MakeTexture',s.mainWindow.winMain,zeros(s.mainWindow.fontSize, s.mainWindow.character_width,4));
                    Screen('TextFont',s.text_textures_box_labels{end},s.mainWindow.fontName);
                    Screen('TextSize',s.text_textures_box_labels{end},floor(0.8*s.mainWindow.fontSize));
                    DrawFormattedText(s.text_textures_box_labels{end}, s.boxes.elements{end}.box_label, 'center', 'center', s.color_past_box);
                    s.boxes.box_being_edited = n_boxes;
                else
                    s.boxes.box_being_edited = None();
                end
            else
                s.boxes.elements{end}.set_active;
                s.boxes.box_being_edited = n_boxes;
            end
            s.state = StatesBBoxCollection.NotEditing;
            s.button_disease.reset_chosen();
            s.button_certainty.reset_chosen();
            s.button_boxes.reset_chosen();
            s.button_save.update_text('Save New Box');
        end
        
        function when_boxchoice_clicked(s)
           if ~None.isNone(s.button_boxes.chosen_index)
               if ~None.isNone(s.boxes.box_being_edited) && ~None.isNone(s.boxes.elements{s.boxes.box_being_edited}.saved_rect)
                    s.boxes.elements{s.boxes.box_being_edited}.discard_reedit_box();
                end
               s.boxes.box_being_edited = s.button_boxes.chosen_index;
               s.state = StatesBBoxCollection.EditingPast;
               properties = s.boxes.elements{s.boxes.box_being_edited}.extra_properties;
               choices = s.button_disease.get_choices();
               chosen = zeros(1,length(choices));
               for ii = 1:length(choices)
                   chosen(ii) = properties(choices{ii});
               end
               s.button_disease.set_chosen(chosen);
               choices = s.button_certainty.get_choices();
               chosen = zeros(1,length(choices));
               for ii = 1:length(choices)
                   chosen(ii) = properties(choices{ii});
               end
               s.button_certainty.set_chosen(chosen);
               if None.isNone(s.boxes.elements{end}.saved_rect)
                    s.boxes.elements{end}.set_inactive;
               end
               s.boxes.elements{s.boxes.box_being_edited}.reedit_box;
               s.button_save.update_text(['Save Box (',s.boxes.elements{s.boxes.box_being_edited}.box_label, ')']);
               s.button_delete.update_text(['Delete Box (',s.boxes.elements{s.boxes.box_being_edited}.box_label,')']);
               s.button_discard.update_text(['Undo Changes (',s.boxes.elements{s.boxes.box_being_edited}.box_label, ')']);
           else
                if ~None.isNone(s.boxes.box_being_edited) && ~None.isNone(s.boxes.elements{s.boxes.box_being_edited}.saved_rect)
                    s.boxes.elements{s.boxes.box_being_edited}.discard_reedit_box();
                end
                s.start_new_box;
            end
        end

        function draw(s, cumulative_drawing)
%             draw@InteractiveCollectionSeveralDepths(s,cumulative_drawing);
             s.draw_disease_selection(cumulative_drawing);
             if s.text_texture_title_button_list_drawn
                 
                Screen('DrawTexture', s.mainWindow.winMain, s.text_texture_title_button_list, [], [10 round(s.centerY+90*s.mainWindow.fontSize/21-s.mainWindow.screenRect(2)+180*s.mainWindow.fontSize/21) 10+17*s.mainWindow.character_width round(s.centerY+90*s.mainWindow.fontSize/21-s.mainWindow.screenRect(2)+2*s.mainWindow.fontSize+180*s.mainWindow.fontSize/21)]);
             end
        end
        
         function draw_disease_selection(s,cumulative_drawing)   
            previous_font_size = s.mainWindow.fontSize;
%             font_size = round(previous_font_size*0.81);
            font_size = previous_font_size;
            current_x = {};
            spacing_chosen = round(0.8*1.15*font_size);
            starting_y = 10;
            startin_x = 10;
            limit_Y = ButtonResetImage.get_rect(s.mainWindow);
            limit_Y = limit_Y(2) - 10;
            
            cumulative_drawing.add_fill_rect(s.depth, [0 0 0], [startin_x starting_y s.mainWindow.margin limit_Y]);
            
            cumulative_drawing.add_texture(s.depth, s.text_texture_title_list,[],[startin_x starting_y 22*s.mainWindow.character_width+startin_x starting_y+s.mainWindow.fontSize ]);

            spacing_count = 1;
            for k=1:length(s.disease_choices)
                cumulative_drawing.add_texture(s.depth, s.text_textures_diseases{k} , [], [startin_x starting_y+spacing_chosen*(spacing_count) s.width_texture_text{k}+startin_x starting_y+spacing_chosen*(spacing_count)+s.mainWindow.fontSize]);
                current_x{end+1} = startin_x+s.width_texture_text{k};
                
                all_indices = s.indices_chosen_disease{k};
                all_indices_certainty = s.indices_certainty_chosen_disease{k};
                
                
                for i=1:length(all_indices)
                    if current_x{k}>=s.mainWindow.margin-1-spacing_chosen
                        spacing_count = spacing_count + 1;
                        current_x{k} = startin_x;
                    end
                    cumulative_drawing.add_texture(s.depth, s.text_textures_box_labels{all_indices(i)}, [], [current_x{k} starting_y+spacing_chosen*(spacing_count) current_x{k}+s.mainWindow.character_width starting_y+spacing_chosen*(spacing_count)+s.mainWindow.fontSize]);
                    current_x{k} = current_x{k} + s.mainWindow.character_width;
                    cumulative_drawing.add_texture(s.depth, s.text_textures_certainty_labels{all_indices_certainty(i)}, [], [current_x{k}-2 starting_y+spacing_chosen*(spacing_count) current_x{k}+s.mainWindow.character_width-2 starting_y+spacing_chosen*(spacing_count)+s.mainWindow.fontSize]);
                    current_x{k} = current_x{k} + 1.5*s.mainWindow.character_width;

                end
                spacing_count = spacing_count + 1; 
                if starting_y+spacing_chosen*(spacing_count)>limit_Y
                    break;
                end
            end
         end
        
         function recalculate_chosen(s)
             s.chosen_diseases_in_box=zeros(1,length(s.chosen_disease));
            [s.indices_chosen_disease{1:length(s.disease_choices)}] = deal([]);
            [s.indices_certainty_chosen_disease{1:length(s.disease_choices)}] = deal([]);
            for k=1:length(s.disease_choices)
                this_list = [];
                this_list_certainty = [];
                for i=1:length(s.boxes.elements)
                    if s.boxes.elements{i}.state~=StatesBBox.Deleted && ~None.isNone(s.boxes.elements{i}.saved_rect)
                        disease_name = s.labels_disease_buttons{k};
                        
                        if s.boxes.elements{i}.extra_properties(disease_name)
                            s.chosen_diseases_in_box(k) = 1;
                            this_list(end+1) = i;
                            this_list_certainty(end+1) = s.boxes.elements{i}.extra_properties('certainty_chosen_index');
                        end
                    end
                end
                s.indices_chosen_disease{k} = this_list;
                s.indices_certainty_chosen_disease{k} = this_list_certainty;
                
            end
         end
    end
end

function when_change_clicked(s, bbox_collection)
    current_box = bbox_collection.boxes.elements{bbox_collection.boxes.box_being_edited};
    if current_box.shape_box == ShapesBBox.Rectangle
       current_box.change_shape(ShapesBBox.Ellipse)
    elseif current_box.shape_box == ShapesBBox.Ellipse
       current_box.change_shape(ShapesBBox.Rectangle)
    end
end

function when_save_clicked(s, bbox_collection, dont_save_box)
    if ~exist('dont_save_box','var')
        dont_save_box = 0;
    end
    if None.isNone(bbox_collection.boxes.elements{bbox_collection.boxes.box_being_edited}.saved_rect) || dont_save_box
       bbox_collection.button_boxes.add_button(bbox_collection.boxes.elements{bbox_collection.boxes.box_being_edited}.box_label, 1);
    end
    
    
    if ~dont_save_box
        data_disease = [containers.Map();containers.Map(bbox_collection.button_disease.get_choices, bbox_collection.button_disease.get_chosen)];
        data_certainty = [containers.Map();containers.Map(bbox_collection.button_certainty.get_choices, bbox_collection.button_certainty.get_chosen)];
        data_certainty('certainty_chosen_string') = bbox_collection.button_certainty.chosen_string;
        data_certainty('certainty_chosen_index') = bbox_collection.button_certainty.chosen_index;
        bbox_collection.boxes.elements{bbox_collection.boxes.box_being_edited}.save_box([data_disease;data_certainty]);
    end
    
    bbox_collection.recalculate_chosen;
    bbox_collection.changed = 1;     
    if ~bbox_collection.text_texture_title_button_list_drawn
%         Screen('DrawTexture',bbox_collection.mainWindow.winMain, bbox_collection.text_texture_title_button_list, [], [10 round(bbox_collection.centerY+90*bbox_collection.mainWindow.fontSize/21-bbox_collection.mainWindow.screenRect(2)) 10+17*bbox_collection.mainWindow.character_width round(bbox_collection.centerY+90*bbox_collection.mainWindow.fontSize/21-bbox_collection.mainWindow.screenRect(2)+2*bbox_collection.mainWindow.fontSize)]);
        bbox_collection.text_texture_title_button_list_drawn = 1;
    end
    
    if ~dont_save_box
        bbox_collection.start_new_box;
    end
end

function when_delete_clicked(s, bbox_collection, dont_delete_box)
    if ~exist('dont_delete_box','var')
        dont_delete_box = 0;
    end
    bbox_collection.changed = 1;
    if ~dont_delete_box
        bbox_collection.boxes.elements{bbox_collection.boxes.box_being_edited}.delete_box();
    end
    bbox_collection.button_boxes.elements{bbox_collection.boxes.box_being_edited}.hide();
    bbox_collection.recalculate_chosen;
    bbox_collection.start_new_box;
end

function when_discard_clicked(s, bbox_collection)
   bbox_collection.boxes.elements{bbox_collection.boxes.box_being_edited}.discard_reedit_box();
   bbox_collection.start_new_box; 
end