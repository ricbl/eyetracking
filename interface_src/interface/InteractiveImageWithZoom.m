classdef InteractiveImageWithZoom < InteractiveImage
    properties
        zoom;
        zoom_previous_update;
        pan_x;
        pan_x_previous_update;
        pan_y;
        pan_y_previous_update;
        zoom_ratio;
        button_index_pan;
        state_pan;
        x_pan_last_update;
        y_pan_last_update;
        zoom_steps;
        max_zoom_steps;
        min_zoom_steps;
    end
    
    methods
        function s = InteractiveImageWithZoom(mainWindow)
            s@InteractiveImage(mainWindow);
            s.reset_zoom;
            s.pan_x_previous_update = s.pan_x;
            s.pan_y_previous_update = s.pan_y;
            s.zoom_previous_update = s.zoom;
            s.zoom_steps = 0;
            s.zoom_ratio = 2^(1/4);
            s.max_zoom_steps = floor(log(70)/log(s.zoom_ratio));
            s.min_zoom_steps = 0;
            s.button_index_pan = 2;
            s.state_pan = StatesInteractiveImage.Waiting;
            
        end        
        
        function reset_zoom(s)
            s.zoom = 1;
            s.zoom_steps = 0;
            s.pan_x = 0;
            s.pan_y = 0;
        end
        
        function reset(s)
            s.reset_zoom;
            s.reset_window;
        end
        
        function interaction = update(s)
            interaction_window = update@InteractiveImage(s);
            changed = interaction_window('changed');
            if s.zoom~=s.zoom_previous_update || s.pan_x~=s.pan_x_previous_update || s.pan_y~=s.pan_y_previous_update
                changed = 1;
                s.structured_output.add_message(class(s),'zoom',s.zoom);
                s.structured_output.add_message(class(s),'pan_x',s.pan_x);
                s.structured_output.add_message(class(s),'pan_y',s.pan_y);
                image_size = [s.image_size_y s.image_size_x];
                rectangle_center_x = s.image_size_x/2;
                rectangle_center_y = s.image_size_y/2;
                rectangle_height = s.available_y_picture/s.scale;
                rectangle_width = s.available_x_picture/s.scale;
                rectangle_height = rectangle_height/s.zoom;
                rectangle_width = rectangle_width/s.zoom;
                rectangle_center_x = rectangle_center_x + s.pan_x;
                rectangle_center_y = rectangle_center_y - s.pan_y;
                source_rect = [rectangle_center_x-rectangle_width/2 rectangle_center_y-rectangle_height/2 rectangle_center_x+rectangle_width/2 rectangle_center_y+rectangle_height/2];
                dimension_cut = [0 0 0 0];
                dest_rect = [s.mainWindow.margin 0 s.available_x_picture+s.mainWindow.margin s.available_y_picture];
                for ii = 1:4
                    previous_dimension = source_rect(ii);
                    source_rect(ii) = max([0, min([source_rect(ii), image_size(mod(ii,2)+1)])]);
                    dimension_cut(ii) = source_rect(ii) - previous_dimension;
                    dest_rect(ii) = dest_rect(ii) + dimension_cut(ii)*s.zoom*s.scale;
                end
                s.source_rect = source_rect;
                s.dest_rect = dest_rect;
                s.save_rects;
            end
            s.zoom_previous_update = s.zoom;
            s.pan_x_previous_update = s.pan_x;
            s.pan_y_previous_update = s.pan_y;
            interaction = containers.Map({'changed', 'exit'}, {changed, ChangeScreen.No});
        end
        
        function apply_zoom(s,wheelDelta,mouse)
            s.zoom_steps = s.zoom_steps - wheelDelta/15;
            if s.zoom_steps<s.min_zoom_steps
                s.apply_delta_pan(s.pan_x/2^(s.min_zoom_steps-s.zoom_steps)-s.pan_x,s.pan_y/2^(s.min_zoom_steps-s.zoom_steps)-s.pan_y);
            end
            s.zoom_steps = min([max([s.min_zoom_steps,s.zoom_steps]),s.max_zoom_steps]);
            old_zoom = s.zoom;
            s.zoom = (s.zoom_ratio^(s.zoom_steps));
            xx = mouse('mouse_x');
            yy = mouse('mouse_y');
            [mouse_image_x,mouse_image_y] = s.convert_screen_to_image_coordinates(xx, yy);
            [corner_image_x,corner_image_y] = s.convert_screen_to_image_coordinates(s.mainWindow.margin, 0);
            [center_image_x,center_image_y] = s.convert_screen_to_image_coordinates(s.mainWindow.margin+s.available_x_picture/2, s.available_y_picture/2);
            delta_pan_x = (mouse_image_x-center_image_x)/(corner_image_x-center_image_x)*((corner_image_x-center_image_x)-(corner_image_x-center_image_x)/s.zoom*old_zoom);
            delta_pan_y = -(mouse_image_y-center_image_y)/(corner_image_y-center_image_y)*((corner_image_y-center_image_y)-(corner_image_y-center_image_y)/s.zoom*old_zoom);
            s.apply_delta_pan(delta_pan_x,delta_pan_y);
        end
        
        function interaction = interact(s, mouse, keyboard)
            interaction_window = interact@InteractiveImage(s,mouse, keyboard);
            wheelDelta = mouse('wheelDelta');
            
            interacted = interaction_window('interacted');
            cursor = interaction_window('cursor');
            if wheelDelta~=0
                interacted = 1;
                s.apply_zoom(wheelDelta,mouse);
            end
            
            xx = mouse('mouse_x');
            yy = mouse('mouse_y');
            [mouse_clicked, mouse_changed_x, mouse_changed_y] = BufferInput.get_indexed_values(mouse, s.button_index_pan);
            
            if None.isNone(mouse_changed_x)
                mouse_changed_x = xx;
            end
            
            if None.isNone(mouse_changed_y)
                mouse_changed_y = yy;
            end
            
            switch(s.state_pan)
                case StatesInteractiveImage.Waiting
                    if mouse_clicked
                        interacted = 1;
                        s.state_pan = StatesInteractiveImage.Changing;
                        s.mouse_down_pan(mouse_changed_x, mouse_changed_y);
                        s.mouse_down_move_pan(xx,yy);
                    end
                case StatesInteractiveImage.Changing
                    interacted = 1;
                    if ~mouse_clicked
                        s.state_pan = StatesInteractiveImage.Waiting;
                    else
                        s.mouse_down_move_pan(xx,yy);
                    end
            end
            interaction = containers.Map({'interacted','cursor'}, {interacted, cursor});
        end
        
        function mouse_down_pan(s, x, y)
            s.x_pan_last_update = x;
            s.y_pan_last_update = y;
        end
        
        function apply_delta_pan(s,delta_pan_x,delta_pan_y)
            s.pan_x = s.pan_x + delta_pan_x; 
            s.pan_x = min([max([-s.image_size_x/2, s.pan_x]), s.image_size_x/2]);
            s.pan_y = s.pan_y + delta_pan_y; 
            s.pan_y = min([max([-s.image_size_y/2, s.pan_y]), s.image_size_y/2]);
        end
        
        function mouse_down_move_pan(s,x,y)
            delta_pan_x = -(x - s.x_pan_last_update)/s.zoom/s.scale;
            delta_pan_y = (y - s.y_pan_last_update)/s.zoom/s.scale;
            s.apply_delta_pan(delta_pan_x,delta_pan_y);
            s.x_pan_last_update = x;
            s.y_pan_last_update = y;
        end
        
    end
end