classdef SegmentManager < InteractiveCollectionSeveralDepths
    properties
        current_index;
        list_of_labels;
        segment_sets;
        texture_middle_screen;
        associated_image;
        total_ribs_per_side;
        text_textures_diseases;
        width_texture_text;
        next_screen;
        x_last_iteraction_move;
        y_last_iteraction_move;
        x_last_iteraction_rotate;
        y_last_iteraction_rotate;
        x_start_iteraction_rotate;
        y_start_iteraction_rotate;
        pressed_hide;
        center_of_ribs;
        x_last_iteraction_scale;
        y_last_iteraction_scale;
        x_start_iteraction_scale;
        y_start_iteraction_scale;
        index_previous_update;
        pressed_hide_previous_update;
        copied_rectangle;
    end
    
    methods
        function s = SegmentManager(mainWindow, associated_image)
            s@InteractiveCollectionSeveralDepths(mainWindow, {}, Depths.text_depth, 'SegmentManager', 1);
%             s.texture_middle_screen = BBoxTexture(s.mainWindow);
            texture_middle_screen = None(); % s.texture_middle_screen;
            s.associated_image = associated_image;
            s.current_index = 3;
            s.index_previous_update = s.current_index;
            s.x_last_iteraction_move = None();
            s.y_last_iteraction_move = None();
            s.x_last_iteraction_rotate = None();
            s.y_last_iteraction_rotate = None();
            s.x_start_iteraction_rotate = None();
            s.y_start_iteraction_rotate = None();
            s.x_last_iteraction_scale = None();
            s.y_last_iteraction_scale = None();
            s.x_start_iteraction_scale = None();
            s.y_start_iteraction_scale = None();
            s.center_of_ribs = {None() None()};
            s.pressed_hide = 0;
            s.copied_rectangle = [];
            s.pressed_hide_previous_update = s.pressed_hide;
            s.total_ribs_per_side = 11;
            s.segment_sets = {};
            s.next_screen = ChangeScreen.No;
            s.list_of_labels = {'Center 1 rib', 'Center 9 rib'};
            s.segment_sets = [s.segment_sets, PolygonSet(mainWindow, s.list_of_labels{1}, associated_image, texture_middle_screen)];
            s.segment_sets = [s.segment_sets, PolygonSet(mainWindow, s.list_of_labels{2}, associated_image, texture_middle_screen)];
            for i = 1:s.total_ribs_per_side
                s.list_of_labels= [s.list_of_labels, {strcat(num2str(i),' rib right')}];
                s.segment_sets = [s.segment_sets, PolygonSet(mainWindow, s.list_of_labels{2+i}, associated_image, texture_middle_screen)];
            end
            for i = 1:s.total_ribs_per_side
                s.list_of_labels= [s.list_of_labels, {strcat(num2str(i),' rib left')}];
                s.segment_sets = [s.segment_sets, PolygonSet(mainWindow, s.list_of_labels{2+s.total_ribs_per_side+i}, associated_image, texture_middle_screen)];
            end
            s.list_of_labels= [s.list_of_labels, {'Next Screen'}];
            s.segment_sets = [s.segment_sets, PolygonSet(mainWindow, s.list_of_labels{2+2*s.total_ribs_per_side+1}, associated_image, texture_middle_screen)];
            
            s.text_textures_diseases = {};
            for i = length(s.list_of_labels):-1:1
                font_multiplier = min([s.mainWindow.margin*0.9/length(s.list_of_labels{i})/s.mainWindow.character_width,0.9]);
                s.width_texture_text{i} = length(s.list_of_labels{i})*floor(s.mainWindow.character_width*font_multiplier);
                s.text_textures_diseases{i} = Screen('MakeTexture', s.mainWindow.winMain, zeros(s.mainWindow.fontSize, s.width_texture_text{i}), 4);
                Screen('TextFont',s.text_textures_diseases{i},s.mainWindow.fontName);
                Screen('TextSize',s.text_textures_diseases{i},floor(floor(s.mainWindow.character_width*font_multiplier)/s.mainWindow.character_width*s.mainWindow.fontSize));
                DrawFormattedText(s.text_textures_diseases{i}, s.list_of_labels{i}, 'center', 'center', [1 1 1 1.25]);
            end
        end
        
        function interaction = before_destruction(s)
            
            for i = 1:length(s.text_textures_diseases)
               Screen('Close', s.text_textures_diseases{i}); 
            end
            for i = 1:length(s.segment_sets)
               s.segment_sets(1,i).before_destruction();
            end
            interaction = containers.Map({'exit'}, {ChangeScreen.NextScreen});
        end   
        
        function interaction = update(s)
            changed = 0;
            if s.current_index~=s.index_previous_update || s.pressed_hide~=s.pressed_hide_previous_update
                changed = 1;
            end
            interaction = s.segment_sets(1,s.current_index).update();
            interaction('changed') = interaction('changed') || changed;
            s.pressed_hide_previous_update = s.pressed_hide;
            s.index_previous_update = s.current_index;
            interaction('exit') = s.next_screen;
        end
        
        function draw(s, cumulative_drawing)
            if ~s.pressed_hide
                s.segment_sets(1,s.current_index).draw(cumulative_drawing);
            end
            s.draw_label_selection(cumulative_drawing)  
        end
        
        function interaction_map = interact(s, mouse, keyboard)
            interaction_set = s.segment_sets(1,s.current_index).interact(mouse,keyboard);
            changed = interaction_set('interacted');
            cursor = 'arrow';%interaction_set('cursor');
            new_char = keyboard('char');
            switch(new_char)
                case 'a'
                    %previous label
                    s.current_index = max(s.current_index - 1, 1);
                case 'd'
                    %next label
                    if s.current_index == 1 || s.current_index == 2
                        if ~isempty(s.segment_sets(1,s.current_index).rect.get_rect)
                            if length(s.segment_sets(1,s.current_index).rect.get_rect)<=2
                                s.center_of_ribs{s.current_index} = mean(s.segment_sets(1,s.current_index).rect.get_rect,1);
                            else
                                this_rect = s.segment_sets(1,s.current_index).rect.get_rect;
                                [cx, cy] = centroid(polyshape(this_rect(:,1),this_rect(:,2)));
                                s.center_of_ribs{s.current_index} = [cx,cy];
                            end
                        end
                    end
                    
                    s.current_index = min(s.current_index + 1, length(s.list_of_labels));
                    
                    if s.current_index>2+s.total_ribs_per_side && s.current_index<=2+2*s.total_ribs_per_side && 0
                        if isempty(s.segment_sets(1,s.current_index).rect.get_rect) && ~None.isNone(s.center_of_ribs{2}) && ~None.isNone(s.center_of_ribs{1})
                            
                            rect_to_reflect = s.segment_sets(1,s.current_index-s.total_ribs_per_side).rect.get_rect;
                            normal = s.center_of_ribs{2}-s.center_of_ribs{1};
                            reflected_rect = [];
                            size_reflected_rect = size(rect_to_reflect);
                            for i = 1:size_reflected_rect
                                point_to_reflect = rect_to_reflect(i,:);
                                b = s.center_of_ribs{1}+normal/norm(normal)^2*dot(normal,point_to_reflect-s.center_of_ribs{1});
                                reflected_point = 2*b-point_to_reflect;
                                reflected_rect = [reflected_rect;reflected_point];
                            end
                            s.segment_sets(1,s.current_index).rect.set_rect(reflected_rect);
                        end
                    end
                    changed = 1;
                case 'w'
                    %zoom in
                    s.associated_image.apply_zoom(-15, mouse);
                case 's'
                    %zoom out
                    s.associated_image.apply_zoom(15, mouse);
                case '2'
                    %reset image
                    s.associated_image.reset()
                case '3'
                    %paste rectangle
                    if ~isempty(s.copied_rectangle)
                        s.segment_sets(1,s.current_index).rect.set_rect(s.copied_rectangle);
                    end
                    %active contours to improve segmentation
%                     preimage = s.segment_sets(1,s.current_index).get_image_array;
%                     BW = activecontour(10*s.associated_image.x,preimage(:,:,1),1,'edge','SmoothFactor',0.2,'ContractionBias',-0.8);
%                     c = bwboundaries(BW','noholes');
%                     s.segment_sets(1,s.current_index).rect.set_rect(c{1});
                case 'c'
                    %copy rectangle
                    s.copied_rectangle = s.segment_sets(1,s.current_index).rect.get_rect;
                case '1'
                    %hide rectangle
                    s.pressed_hide = 1 - s.pressed_hide;
                case 'r'
                    %reset rectangle
                    s.segment_sets(1,s.current_index).reset()
                case ' '
                    if s.current_index==length(s.list_of_labels)
                        %next screen
                         s.next_screen = ChangeScreen.NextScreen;
                    else
                        %change color
                        s.segment_sets(1,s.current_index).switch_color;
                        changed = 1;
                    end
                case 'q'  %undo 
                    s.segment_sets(1,s.current_index).undo_rect;
                    changed = 1;
                case 'e' %redo
                    s.segment_sets(1,s.current_index).redo_rect;
                    changed = 1;
            end
            %if shift pressed, mouse moves drawing
            [~, ~, keyboard, ~] = KbCheck();
            if keyboard(KbName('LeftShift'))
                if None.isNone(s.x_last_iteraction_move)
                    delta_x = 0;
                else
                    delta_x = mouse('mouse_x') - s.x_last_iteraction_move;
                end
                if None.isNone(s.y_last_iteraction_move)
                    delta_y = 0;
                else
                    delta_y = mouse('mouse_y') - s.y_last_iteraction_move;
                end
                s.segment_sets(1,s.current_index).move(delta_x, delta_y);
                s.x_last_iteraction_move = mouse('mouse_x');
                s.y_last_iteraction_move = mouse('mouse_y');
            else
                s.x_last_iteraction_move = None();
                s.y_last_iteraction_move = None();
            end
            
            if keyboard(KbName('LeftAlt'))
                if None.isNone(s.x_last_iteraction_scale)
                    delta_x = 0;
                    s.x_start_iteraction_scale = mouse('mouse_x');
                else
                    delta_x = mouse('mouse_x') - s.x_last_iteraction_scale;
                end
                if None.isNone(s.y_last_iteraction_scale)
                    delta_y = 0;
                    s.y_start_iteraction_scale = mouse('mouse_y');
                else
                    delta_y = mouse('mouse_y') - s.y_last_iteraction_scale;
                end
                s.segment_sets(1,s.current_index).scale(delta_x, -delta_y, s.x_start_iteraction_scale,s.y_start_iteraction_scale);
                s.x_last_iteraction_scale = mouse('mouse_x');
                s.y_last_iteraction_scale = mouse('mouse_y');
            else
                s.x_last_iteraction_scale = None();
                s.y_last_iteraction_scale = None();
                s.x_start_iteraction_scale = None();
                s.y_start_iteraction_scale = None();
            end
            
            if keyboard(KbName('LeftControl'))
                if None.isNone(s.x_last_iteraction_rotate)
                    delta_x = 0;
                    s.x_start_iteraction_rotate = mouse('mouse_x');
                else
                    delta_x = mouse('mouse_x') - s.x_last_iteraction_rotate;
                end
                if None.isNone(s.y_last_iteraction_rotate)
                    delta_y = 0;
                    s.y_start_iteraction_rotate = mouse('mouse_y');
                else
                    delta_y = mouse('mouse_y') - s.y_last_iteraction_rotate;
                end
                s.segment_sets(1,s.current_index).rotate(delta_x, s.x_start_iteraction_rotate,s.y_start_iteraction_rotate);
                s.x_last_iteraction_rotate = mouse('mouse_x');
                s.y_last_iteraction_rotate = mouse('mouse_y');
            else
                s.x_last_iteraction_rotate = None();
                s.y_last_iteraction_rotate = None();
                s.x_start_iteraction_rotate = None();
                s.y_start_iteraction_rotate = None();
            end
            
            interaction_map = containers.Map({'interacted', 'cursor'}, { changed, cursor});
        end
        
         function draw_label_selection(s,cumulative_drawing)   
            font_size = s.mainWindow.fontSize;
            spacing_chosen = round(0.8*1.15*font_size);
            starting_y = 10;
            startin_x = s.mainWindow.screenRect(3)-s.mainWindow.margin+10;
            limit_Y = s.mainWindow.screenRect(4) - 10;
            cumulative_drawing.add_fill_rect(s.depth, [0 0 0], [startin_x starting_y s.mainWindow.screenRect(3)-10 limit_Y]);
            
            spacing_count = 1;
            for k=1:length(s.list_of_labels)
                cumulative_drawing.add_texture(s.depth, s.text_textures_diseases{k} , [], [startin_x starting_y+spacing_chosen*(spacing_count) s.width_texture_text{k}+startin_x starting_y+spacing_chosen*(spacing_count)+s.mainWindow.fontSize]);
                if k == s.current_index
                    cumulative_drawing.add_frame_rect(s.depth, [1 0 0], [startin_x starting_y+spacing_chosen*(spacing_count) s.width_texture_text{k}+startin_x starting_y+spacing_chosen*(spacing_count)+s.mainWindow.fontSize]);
                end
                spacing_count = spacing_count + 1; 
                if starting_y+spacing_chosen*(spacing_count)>limit_Y
                    break;
                end
            end
         end
        
    end
    
end

function reflect(coordinate, normal)
    coordinate = coordinate - 2*(coordinate(1)*normal(1)+coordinate(2)*normal(2))*normal;
end