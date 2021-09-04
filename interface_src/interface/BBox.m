classdef BBox < InteractiveTemplate
    properties(Constant)
       labels_array = {'A','B','C', 'D', 'E', 'F','G','H','I','J','K','L','M','N','P','Q','R','S','T','U','V','W','X','Y','Z','a','b','d','e','f','g','h','m','n','q','r','t','æ','Æ','@','#','%','$','£','¥','§','Ø','β','ζ','θ','δ','λ','ξ','π','φ','ψ','Δ','Λ','Ξ','Π','Σ','Ω','©','®','¬','«','»','!','õ','ñ','Ñ','â','ê','ü','ÿ','ï'}; 
    end
    properties
       state; 
       rect;
       saved_rect;
       saved_shape;
       margin;
       modifying;
       extra_properties;
       box_id;
       box_label;
       rect_previous_update;
       state_previous_update;
       horizontal_coord;
       horizontal_coord_previous_update;
       vertical_coord;
       vertical_coord_previous_update;
       block_next;
       shape_box;
       associated_image;
       mouse_button_index;
       label_texture;
       manage_texture_redrawing;
       cross_texture;
       texture_middle_screen;
       zoom_previous_update;
       pan_x_previous_update;
       pan_y_previous_update;
       delta_margin;
       bbox_from_center;
       shape_box_previous_update;
    end
    methods
        
        function s = BBox(mainWindow, box_id, block_next, associated_image, shape_box, texture_middle_screen)
            s@InteractiveTemplate(Depths.box_depth, strcat('BBox_',num2str(box_id)), mainWindow, 1);
            s.associated_image = associated_image;
            s.reset_zoom_previous_update;
            s.label_texture = None();
            if None.isNone(texture_middle_screen)
                s.texture_middle_screen = BBoxTexture(s.mainWindow);
                s.manage_texture_redrawing = 1;
            else
                s.manage_texture_redrawing = 0;
                s.texture_middle_screen = texture_middle_screen;
            end
            s.cross_texture = None();
            if box_id == 0
                s.box_label = '';
            else
                s.box_label = BBox.labels_array{box_id};
            end

            s.rect_previous_update = [0 0 0 0];
            s.state = StatesBBox.Discarded;
            s.state_previous_update = s.state;
            s.saved_rect = None();
            s.saved_shape = None();
            s.block_next = block_next;
            s.margin = 30*mainWindow.fontSize/22;
            s.modifying={0,0,0,0};
            s.delta_margin = [0 0 0 0];
            s.box_id = box_id;
            s.horizontal_coord = None();
            s.vertical_coord = None();
            s.horizontal_coord_previous_update = None();
            s.vertical_coord_previous_update = None();
            s.extra_properties = containers.Map();
            s.shape_box = shape_box;
            s.shape_box_previous_update = shape_box;
            s.mouse_button_index = 1;
            s.bbox_from_center = 0;
        end
        
        function change_shape(s,shape_dest)
            s.shape_box = shape_dest;
        end
        
        function load_state(s, state)
            s.rect = state('rect');
            s.extra_properties = state('extra_properties');
            s.saved_rect = state('saved_rect');
            s.state = state('state');
            s.saved_shape = state('saved_shape');
            s.initialize_label_texture;
        end
        
        function state = save_state(s)
            state = containers.Map();
            state('rect') = s.rect;
            state('extra_properties') = s.extra_properties;
            state('saved_rect') = s.saved_rect;
            state('state') = s.state;
            state('saved_shape') = s.saved_shape;
        end
        
        function reset_zoom_previous_update(s)
            if isprop(s.associated_image,'zoom')
                s.zoom_previous_update = s.associated_image.zoom;
                s.pan_x_previous_update = s.associated_image.pan_x;
                s.pan_y_previous_update = s.associated_image.pan_y; 
            else
                s.zoom_previous_update = 0;
                s.pan_x_previous_update = 0;
                s.pan_y_previous_update = 0 ;
            end
        end
        
        function interaction_map = update(s)
            changed = 0;
            if ~isequal(s.shape_box, s.shape_box_previous_update)
                changed = 1;
                s.texture_middle_screen.texture_changed_last_update = 1;
            end
            if ~isequal(s.rect, s.rect_previous_update) ...
                    || ~isequal(s.state, s.state_previous_update)
                s.texture_middle_screen.texture_changed_last_update = 1;
                changed = 1;
            end
            if isprop(s.associated_image,'zoom')
                if ~isequal(s.associated_image.zoom, s.zoom_previous_update) ...
                        || ~isequal(s.associated_image.pan_x, s.pan_x_previous_update) ...
                        || ~isequal(s.associated_image.pan_y, s.pan_y_previous_update)
                    s.texture_middle_screen.texture_changed_last_update = 1;
                end
            end
                
            if ~isequal(s.horizontal_coord,s.horizontal_coord_previous_update) ...
                    || ~isequal(s.vertical_coord,s.vertical_coord_previous_update)
                changed = 1;
            end
            
            s.shape_box_previous_update = s.shape_box;
            s.rect_previous_update = s.rect;
            s.state_previous_update = s.state;
            s.horizontal_coord_previous_update = s.horizontal_coord;
            s.vertical_coord_previous_update = s.vertical_coord;
            s.reset_zoom_previous_update;
            if s.block_next
                switch(s.state)
                    case {StatesBBox.Discarded}
                        s.parent.get_element_by_name('ButtonNext').set_inactive;
                        s.parent.get_element_by_name('ButtonBack').set_inactive;
                    case {StatesBBox.Editing,StatesBBox.Saved,StatesBBox.Editable}
                        s.parent.get_element_by_name('ButtonNext').unset_inactive;
                        s.parent.get_element_by_name('ButtonBack').unset_inactive;
                end
            end
            interaction_map = containers.Map({'changed', 'exit'}, {changed, ChangeScreen.No});
        end
        
        function return_value = is_inside_margins(s,x,y)
            return_value = x>s.mainWindow.margin && x<(s.mainWindow.screenRect(3)-s.mainWindow.margin-s.mainWindow.screenRect(1));
        end
        
        function update_coords(s,xx,yy)
            if s.is_inside_margins(xx,yy)
                s.vertical_coord = xx;
                s.horizontal_coord = yy;
            else
                s.vertical_coord = None();
                s.horizontal_coord = None();
            end
        end
        
        function update_rect(s, xx, yy)
            for i=1:4
                if s.modifying{i}
                    if mod(i,2)
                        coord = xx;
                    else
                        coord = yy;
                    end
                    s.rect(i) = coord - s.delta_margin(i);
                end
            end
        end
        
        function to_return = get_delta_margin(s,coord,i)
            to_return = coord - s.rect(i);
        end
        
        function interaction_map = interact(s,mouse, ~) 
            xx = mouse('mouse_x');
            yy = mouse('mouse_y');
            screen_xx = xx;
            screen_yy = yy;
            [mouse_clicked, mouse_changed_x, mouse_changed_y] = BufferInput.get_indexed_values(mouse, s.mouse_button_index);
            if None.isNone(mouse_changed_x)
                mouse_changed_x = xx;
            end
            if None.isNone(mouse_changed_y)
                mouse_changed_y = yy;
            end
            [xx,yy] = s.associated_image.convert_screen_to_image_coordinates(xx,yy);
            [mouse_changed_x,mouse_changed_y] = s.associated_image.convert_screen_to_image_coordinates(mouse_changed_x,mouse_changed_y);
            
            cursor = '';
            
            interacted = 0;
            interaction_map = containers.Map({'interacted','cursor'}, {0, ''});
            switch(s.state)
                case StatesBBox.Saved
                    return;
                case StatesBBox.Deleted
                    return;
            end
            
            if s.is_inside_margins(screen_xx,screen_yy)
                switch(s.state)
                    case StatesBBox.Editing
                        cursor = 'hand';
                        if mouse_clicked
                            interacted = 1;
                            s.update_rect(xx,yy);
                        else
                            interacted = 1;
%                             s.update_rect(mouse_changed_x,mouse_changed_y);
                            if (s.rect(1)==s.rect(3)) || (s.rect(2)==s.rect(4))
                                s.state = StatesBBox.Discarded;
                            else
                                s.state = StatesBBox.Editable;
                            end
                        end
                    case StatesBBox.Editable
                        if mouse_clicked
                            interacted = 1;
                            s.state = StatesBBox.Editing;
                            cursor = 'hand';
                            s.vertical_coord = None();
                            s.horizontal_coord = None();
                            if s.is_over_rect(mouse_changed_x,mouse_changed_y)
                                current_mouse_coords = [xx yy];
                                starting_coords = [mouse_changed_x,mouse_changed_y];
                                if s.is_over_(5,mouse_changed_x,mouse_changed_y)
                                    s.modifying = {1,1,1,1};
                                    for i=1:4
                                        s.delta_margin(i) = s.get_delta_margin(starting_coords(mod(i-1,2)+1),i);
                                        s.rect(i) = current_mouse_coords(mod(i-1,2)+1) - s.delta_margin(i);
                                    end
                                else
                                    for i=1:2
                                        s.modifying{i} = s.is_over_(i,mouse_changed_x,mouse_changed_y);
                                        if ~s.modifying{i}
                                            s.modifying{i+2} = s.is_over_(i+2,mouse_changed_x,mouse_changed_y);
                                            if s.modifying{i+2}
                                                s.delta_margin(i+2) = s.get_delta_margin(starting_coords(i), i+2);
                                                s.rect(i+2) = current_mouse_coords(i) - s.delta_margin(i+2);
                                                s.delta_margin(i) = 0;
                                            end
                                        else

                                            s.delta_margin(i) = s.get_delta_margin(starting_coords(i),i);
                                            s.rect(i) = current_mouse_coords(i) - s.delta_margin(i);
                                            s.modifying{i+2} = false;
                                            s.delta_margin(i+2) = 0;
                                        end
                                    end
                                end
                            else
                                s.rect = [mouse_changed_x mouse_changed_y xx yy];
                                s.modifying = {0,0,1,1};
                                s.delta_margin = [0 0 0 0];
                            end                    
                        else
                            if s.is_over_rect(xx,yy)
                                cursor = 'hand';
                                s.vertical_coord = None();
                                s.horizontal_coord = None();
                            else
                                s.update_coords(screen_xx,screen_yy);
                            end
                        end
                    case StatesBBox.Discarded
                        if mouse_clicked
                            interacted = 1;
                            s.rect = [mouse_changed_x mouse_changed_y xx yy];
                            s.state = StatesBBox.Editing;
                            s.modifying = {0,0,1,1};
                            s.delta_margin = [0 0 0 0];
                            cursor = 'hand';
                            s.vertical_coord = None();
                            s.horizontal_coord = None();
                        else
                            s.update_coords(screen_xx,screen_yy);
                        end
                end
            else
                s.vertical_coord = None();
                s.horizontal_coord = None();
            end
            interaction_map = containers.Map({'interacted','cursor'}, {interacted, cursor});
        end
        
        function rect_ = convert_rect_to_image(s,rect)
            [rect_1, rect_2] = s.associated_image.convert_screen_to_image_coordinates(rect(1),rect(2));
            [rect_3, rect_4] = s.associated_image.convert_screen_to_image_coordinates(rect(3),rect(4));
            rect_ = [rect_1, rect_2, rect_3, rect_4];
        end
        
        function rect_ = convert_saved_rect_to_screen(s, rect)
            [rect_1,rect_2] = s.associated_image.convert_image_to_screen_coordinates(rect(1), rect(2));
            [rect_3,rect_4] = s.associated_image.convert_image_to_screen_coordinates(rect(3), rect(4));
            rect_ = [rect_1, rect_2, rect_3, rect_4];
        end
        
        function initialize_label_texture(s)
            if None.isNone(s.label_texture)
                s.label_texture = Screen('MakeTexture',s.mainWindow.winMain,zeros(s.mainWindow.fontSize, s.mainWindow.character_width,4));
                Screen('TextFont',s.label_texture,s.mainWindow.fontName);
                Screen('TextSize',s.label_texture,s.mainWindow.fontSize);
                DrawFormattedText(s.label_texture, s.box_label, 'center', 'center', [0 1 0 2]);
            end
        end
        
        function save_box(s, extra_properties)
            
            s.initialize_label_texture;        
            if exist('extra_properties','var')
                s.extra_properties = [s.extra_properties;extra_properties];
            end
            s.structured_output.add_message(s.parent.name,'save_box',s.box_id);
            s.saved_rect = s.rect;
            s.saved_shape = s.shape_box;
            s.rect = None();
            s.state = StatesBBox.Saved;
            s.vertical_coord = None();
            s.horizontal_coord = None();
        end
        
        function set_inactive(s)
            s.state = StatesBBox.Inactive;
            s.vertical_coord = None();
            s.horizontal_coord = None();
        end
        
        function set_active(s)
            s.state = StatesBBox.Discarded;
            s.vertical_coord = None();
            s.horizontal_coord = None();
        end
        
        function reedit_box(s)
            s.structured_output.add_message(s.parent.name,'reedit_box',s.box_id);
            s.rect = s.saved_rect;
            s.shape_box = s.saved_shape;
            s.state = StatesBBox.Editable;
        end
        
        function discard_reedit_box(s)
            s.structured_output.add_message(s.parent.name,'discard_reedit_box',s.box_id);
            s.rect = None();
            s.state = StatesBBox.Saved;
        end
        
        function delete_box(s)
            s.structured_output.add_message(s.parent.name,'delete_box',s.box_id);
            s.state = StatesBBox.Deleted;
            s.vertical_coord = None();
            s.horizontal_coord = None();
        end
        
        function return_value = is_over_(s,i,x,y)
            return_value = false;
            if ~None.isNone(s.rect)
                y_max = max([ s.rect(2) s.rect(4)]);
                y_min = min([ s.rect(2) s.rect(4)]);
                x_max = max([ s.rect(1) s.rect(3)]);
                x_min = min([ s.rect(1) s.rect(3)]);
                
                %check proximity to center 
                x_center = (s.rect(1)+s.rect(3))/2;
                y_center = (s.rect(2)+s.rect(4))/2;
                [x_radius,y_radius] = s.get_radius_classic_bbox(s.rect);
                if s.hit(abs(x-x_center),abs(y-y_center),0,0, x_radius/2, y_radius/2)
                    if i==5 && s.hit(abs(x-x_center),abs(y-y_center),0,0, s.margin, s.margin)
                        return_value = true;
                    end
                    return;
                end
                if i==5
                    return;
                end
                if i==2 || i==4
                    
                    if abs(y-s.rect(i))>abs(y-s.rect(mod(i+1, 4)+1))
                        return;
                    end
                    if x>=x_min && x<=x_max
                        distance_even = abs(y - s.rect(i));
                    elseif x<x_min 
                        if x_min-x<=s.margin
                            distance_even = pdist([x,y;x_min,s.rect(i)],'euclidean');
                        else
                            return
                        end
                    elseif x-x_max<=s.margin
                        distance_even = pdist([x,y;x_max,s.rect(i)],'euclidean');
                    else
                        return
                    end
                    if distance_even<=s.margin
                        return_value = true;
                    end
                    return
                else
                    
                    if abs(x-s.rect(i))>abs(x-s.rect(mod(i+1, 4)+1))
                        return;
                    end
                    if y>=y_min && y<=y_max
                        distance_odd = abs(x - s.rect(i));
                    elseif y<y_min 
                        if y_min-y<=s.margin
                            distance_odd = pdist([x,y;s.rect(i), y_min],'euclidean');
                        else
                            return
                        end
                    elseif y-y_max<=s.margin
                        distance_odd = pdist([x,y;s.rect(i), y_max],'euclidean');
                    else
                        return
                    end
                    if distance_odd<=s.margin
                        return_value = true;
                    end
                    return
                end
            end
        end 
        
        function return_value = is_over_rect(s,x,y)
           return_value = s.is_over_(1,x,y) | ...
                s.is_over_(2,x,y) | ...
                s.is_over_(3,x,y) | ...
                s.is_over_(4,x,y) | ...
                s.is_over_(5,x,y);
        end 
        
        function ishit = hit(s,x,y, x_min,y_min,x_max,y_max)
           ishit = x<=x_max & x >=x_min & y >= y_min & y <=y_max;
        end
        
        function [x,y] = get_label_coordinates(s,rect, shape)
            rect_ = s.convert_saved_rect_to_screen(rect);
            rect_1 = rect_(1);
            rect_2 = rect_(2);
            rect_3 = rect_(3);
            rect_4 = rect_(4);
            switch(shape)
                case ShapesBBox.Ellipse
                    y = round((rect_2+rect_4)/2-s.mainWindow.fontSize/2);
                case ShapesBBox.Rectangle
                    y = min([rect_2,rect_4])+4;
            end
            x = min([rect_1,rect_3])+4;
        end
        
        function draw_cut_texture(s, texture, x, y)
            [texture_width, texture_height] = Screen('WindowSize', texture);
            dest_rect = [x-s.mainWindow.margin y x+texture_width-s.mainWindow.margin y+texture_height];
            [texture_middle_width, texture_middle_height] = Screen('WindowSize', s.texture_middle_screen.texture_index);
             texture_limits = [0 0 texture_middle_width texture_middle_height];
            [~, residuals] = BBox.get_cut_residuals(dest_rect, texture_limits);
            source_rect = [0 0 texture_width texture_height] - residuals;
            if source_rect(3)-source_rect(1)>0 && source_rect(4)-source_rect(2)>0  
                Screen('DrawTexture', s.texture_middle_screen.texture_index, texture, source_rect, dest_rect);
            end
        end
        
        function draw(s, cumulative_drawing)
            if s.state~=StatesBBox.Saved && s.state~=StatesBBox.Deleted && s.state~=StatesBBox.Inactive
                if ~None.isNone(s.horizontal_coord)
                    cumulative_drawing.add_line(s.depth, [0.5,0.5,0.5,0.5], s.mainWindow.margin, s.horizontal_coord, s.mainWindow.screenRect(3)-s.mainWindow.screenRect(1)-s.mainWindow.margin, s.horizontal_coord ,0.0625*s.mainWindow.fontSize);
                end
                if ~None.isNone(s.vertical_coord)
                    cumulative_drawing.add_line(s.depth, [0.5,0.5,0.5,0.5], s.vertical_coord, 0, s.vertical_coord, s.mainWindow.screenRect(4)-s.mainWindow.screenRect(2) ,0.0625*s.mainWindow.fontSize);
                end
            end
            if s.texture_middle_screen.texture_changed_last_update
                if s.manage_texture_redrawing
                    s.texture_middle_screen.reset_texture();
                end
                if s.state~=StatesBBox.Deleted && s.state~=StatesBBox.Inactive
                    if ~None.isNone(s.saved_rect)
                        s.draw_rect([0 1 0 0.8], s.saved_rect, s.saved_shape, 0,1, cumulative_drawing);
                        [x_label,y_label] = s.get_label_coordinates(s.saved_rect, s.saved_shape);
                        s.draw_cut_texture(s.label_texture, x_label, y_label);

                    end

                    if  s.state~=StatesBBox.Saved && s.state~=StatesBBox.Discarded
                        s.draw_rect([1 0 0 1.25], s.rect,s.shape_box, 1,0, cumulative_drawing);
                    end

                end
                
            end
            if s.manage_texture_redrawing
                s.texture_middle_screen.texture_changed_last_update = 0;
                [texture_width, texture_height] = Screen('WindowSize',s.texture_middle_screen.texture_index);
                cumulative_drawing.add_texture(s.depth, s.texture_middle_screen.texture_index, [], [s.mainWindow.margin 0 s.mainWindow.margin+texture_width texture_height]);
            end
        end
        
        function [x_radius,y_radius] = get_radius_classic_bbox(s, rect)
            x_radius = abs(rect(3) - rect(1))/2;
            y_radius = abs(rect(4) - rect(2))/2;
        end
                        
        function  [x_center, y_center] = get_center(s, rect)
            x_center = (rect(1)+rect(3))/2;
            y_center = (rect(2)+rect(4))/2;
        end
        
        function on_screen = test_ellipse_on_screen(s, rect, rect_limits)
            [x_center, y_center] = s.get_center(rect);
            distance = [];
            corner_points = [[x_center, rect_limits(4)];[x_center, rect_limits(2)];[rect_limits(3), y_center];[rect_limits(1), y_center];[rect_limits(1), rect_limits(2)];[rect_limits(1), rect_limits(4)];[rect_limits(3), rect_limits(2)];[rect_limits(3), rect_limits(4)]];
            for i = length(corner_points):-1:1
                if ~s.hit(corner_points(i,1), corner_points(i,2), rect_limits(1), rect_limits(2), rect_limits(3), rect_limits(4))
                    corner_points(i,:) = [];
                end
            end
            for i = length(corner_points):-1:1
                distance(i) = norm([x_center, y_center]-corner_points(i,:));
            end
            [~, index_min_distance] = min(distance);
            [~, index_max_distance] = max(distance);
            [x_radius,y_radius] = s.get_radius_classic_bbox(rect);
            relative_to_max_distance = s.get_ellipse_position_relative_to_point(corner_points(index_max_distance,1),corner_points(index_max_distance,2),x_center,y_center,x_radius,y_radius);
            if s.hit(x_center, y_center, rect_limits(1), rect_limits(2), rect_limits(3), rect_limits(4))
                on_screen = relative_to_max_distance >= 1;
            else
                relative_to_min_distance = s.get_ellipse_position_relative_to_point(corner_points(index_min_distance,1),corner_points(index_min_distance,2),x_center,y_center,x_radius,y_radius);
                on_screen = relative_to_min_distance <= 1 && relative_to_max_distance >= 1;
            end
        end
        
        function return_value = get_ellipse_position_relative_to_point(s,x,y,x_center,y_center,x_radius,y_radius)
            return_value = (x-x_center)^2/(x_radius)^2+(y-y_center)^2/(y_radius)^2;
        end
        
        function draw_rect(s, color, rect, shape, draw_crosses, is_saved_rect, cumulative_drawing)
            rect_ = s.convert_saved_rect_to_screen(rect);
            rect_1 = round(rect_(1));
            rect_2 = round(rect_(2));
            rect_3 = round(rect_(3));
            rect_4 = round(rect_(4));
            if rect_2~=rect_4 && rect_1~=rect_3
                dest_rect = [min([rect_1 rect_3]) min([rect_2 rect_4]) max([rect_1 rect_3]) max([rect_2 rect_4])];
                rect_limits = [s.mainWindow.margin 0 s.mainWindow.screenRect(3)-s.mainWindow.screenRect(1)-s.mainWindow.margin  s.mainWindow.screenRect(4)-s.mainWindow.screenRect(2)];
                [dest_rect, residuals] = BBox.get_cut_residuals(dest_rect, rect_limits);
                if dest_rect(4)>dest_rect(2) && dest_rect(3)>dest_rect(1) && ((shape==ShapesBBox.Ellipse && s.test_ellipse_on_screen(rect_, rect_limits))  || (shape==ShapesBBox.Rectangle && any(residuals==0)))
                    rect_location = [0 0 max([rect_1 rect_3])-min([rect_1 rect_3]) max([rect_2 rect_4])-min([rect_2 rect_4])]+[residuals(1) residuals(2) residuals(1) residuals(2)];
                    rect_texture = Screen('MakeTexture', s.mainWindow.winMain, zeros(dest_rect(4)-dest_rect(2), dest_rect(3)-dest_rect(1),4));
                    switch(shape)
                        case ShapesBBox.Ellipse
                            eccentricity = (max([rect_1 rect_3])-min([rect_1 rect_3]))/(max([rect_2 rect_4])-min([rect_2 rect_4]));
                            if eccentricity<1
                                eccentricity = 1/eccentricity;
                            end

                            Screen('FrameOval', rect_texture, color, ...
                                rect_location,...
                                shape.get_thickness/32*s.mainWindow.fontSize*eccentricity);
                            if shape==ShapesBBox.Ellipse && draw_crosses
                                s.draw_cross(color, rect_1, rect_2, cumulative_drawing);
                                s.draw_cross(color, rect_1, rect_4, cumulative_drawing);
                                s.draw_cross(color, rect_3, rect_2, cumulative_drawing);
                                s.draw_cross(color, rect_3, rect_4, cumulative_drawing);
                            end
                        case ShapesBBox.Rectangle
                            Screen('FrameRect', rect_texture, color, ...
                                rect_location,...
                                shape.get_thickness/32*s.mainWindow.fontSize);
                    end
                    [x_center,y_center] = s.get_center(rect_);
                    if draw_crosses
                        s.draw_cross(color, x_center, y_center,cumulative_drawing);
                    end
                    
                    s.draw_cut_texture(rect_texture,max([min([rect_1 rect_3]),rect_limits(1)]), max([min([rect_2 rect_4]),rect_limits(2)]));

                     Screen('Close',rect_texture); 
                end
            end
        end
        
        function interaction_map = before_destruction(s)
            s.mainWindow.states([num2str(s.mainWindow.screen_i), '_', s.name]) = s.save_state;
            if s.block_next
                s.save_box;
            end
            if ~None.isNone(s.saved_rect)
                s.structured_output.add_message(s.parent.name,'saving_box_parameters', s.box_id);
                s.structured_output.add_message(s.parent.name,['box_',num2str(s.box_id),'_from_center'], s.bbox_from_center);
                s.structured_output.add_message(s.parent.name,['box_',num2str(s.box_id),'_type'], s.saved_shape.get_frame_string);
                if ~None.isNone(s.saved_rect)
                    for k=1:4
                        s.structured_output.add_message(s.parent.name,['box_',num2str(s.box_id),'_dimension_',num2str(k)], s.saved_rect(k));
                    end
                end
                extra_properties_keys = keys(s.extra_properties);
                s.structured_output.add_message(s.parent.name,['extra_properties_total_indexes_box_',num2str(s.box_id)], length(extra_properties_keys));
                for ii = 1:length(extra_properties_keys)
                    s.structured_output.add_message(s.parent.name,['extra_properties_key_box_',num2str(s.box_id),'_index_', num2str(ii)], extra_properties_keys{ii});
                    s.structured_output.add_message(s.parent.name,['extra_properties_value_box_',num2str(s.box_id),'_index_',num2str(ii)], s.extra_properties(extra_properties_keys{ii}));
                end
                s.structured_output.add_message(s.parent.name,['box_',num2str(s.box_id),'_deleted'], s.state==StatesBBox.Deleted);
            end
             
            if ~None.isNone(s.label_texture)
                Screen('Close',s.label_texture);
            end
            if ~None.isNone(s.cross_texture)
                Screen('Close',s.cross_texture);
            end
            if s.manage_texture_redrawing
                Screen('Close',s.texture_middle_screen.texture_index);
            end
            interaction_map = containers.Map({'exit'}, {ChangeScreen.No});
        end   
        
        function draw_cross(s,color, x_center, y_center,cumulative_drawing)
            length_arm = ceil(0.2*s.mainWindow.fontSize);
            if None.isNone(s.cross_texture)
                thickness = ceil(0.08*s.mainWindow.fontSize);
                s.cross_texture = Screen('MakeTexture', s.mainWindow.winMain,zeros(length_arm*2,length_arm*2,4));
                Screen('DrawLine', s.cross_texture,color, length_arm, 0, length_arm, 2*length_arm ,thickness);
                Screen('DrawLine', s.cross_texture, color, 2*length_arm, length_arm, length_arm+thickness/2, length_arm ,thickness);
                Screen('DrawLine', s.cross_texture, color, length_arm-thickness/2, length_arm, 0, length_arm ,thickness);
            end
            s.draw_cut_texture(s.cross_texture, x_center - length_arm, y_center - length_arm );
        end
        
    end
    
    methods(Static)
        function [rect_, residuals] = get_cut_residuals(rect, rect_limits)
            residuals = [0 0 0 0];
            rect_ = rect;
            if rect(1)<rect_limits(1)
                residuals(1) = rect(1) - rect_limits(1);
                rect_(1) = rect_limits(1);
            end
            if rect(2)<rect_limits(2)
                residuals(2) = rect(2) - rect_limits(2);
                rect_(2) = rect_limits(2);
            end
            if rect(3)>rect_limits(3)
                residuals(3) = rect(3) - rect_limits(3)  ;
                rect_(3) = rect_limits(3);
            end
            if rect(4)>rect_limits(4)
                residuals(4) = rect(4) - rect_limits(4);
                rect_(4) = rect_limits(4);
            end
        end
    end
end