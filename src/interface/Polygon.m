classdef Polygon < handle
    properties
       state; 
       rect_previous_update;
       state_previous_update;
       associated_image;
       mouse_button_index;
       color;
       current_rect_texture_index;
       rect_texture_changed;
       future_lines;
       commands_past;
       commands_future;
       mainWindow;
       past_lines;
    end
    properties  (Access = private)
      rect;
   end
    methods
        
        function s = Polygon(mainWindow, associated_image, color)
            s.mainWindow = mainWindow;
            s.associated_image = associated_image;
            s.color = color;
            s.rect = [];
            s.state = StatesBBox.Editing;
            s.state_previous_update = s.state;
            s.mouse_button_index = 1;
            s.current_rect_texture_index = None();
            s.rect_texture_changed = 0;
            s.future_lines = {};
            s.past_lines = {};
            s.commands_past = {};
            s.commands_future = {};
        end

        function changed = update(s)
            changed = 0;
            if ~isequal(s.rect, s.rect_previous_update) ...
                    || ~isequal(s.state, s.state_previous_update)
                s.rect_texture_changed = 1;
                changed = 1;
            end
            s.rect_previous_update = s.rect;
            s.state_previous_update = s.state;
            
        end
        
        function return_value = is_inside_margins(s,x,y)
            return_value = x>s.mainWindow.margin && x<(s.mainWindow.screenRect(3)-s.mainWindow.margin-s.mainWindow.screenRect(1));
        end
        
        function move(s, delta_x, delta_y)
            delta_x=delta_x/s.associated_image.zoom/s.associated_image.scale;
            delta_y=delta_y/s.associated_image.zoom/s.associated_image.scale;
            if ~isempty(s.commands_past) && strcmp(s.commands_past{end},'move')
                s.past_lines{end} = s.past_lines{end} + [delta_x, delta_y];
            else
                s.past_lines = {s.past_lines, [delta_x, delta_y]};
                s.commands_past = {s.commands_past, 'move'};
            end
            
            s.move_(delta_x, delta_y);
            
            s.future_lines = {};
            s.commands_future = {};
%             s.last_xx = s.last_xx + delta_x;
%             s.last_yy = s.last_yy + delta_y;
        end
        
        function move_(s, delta_x, delta_y)
            s.rect = s.rect + [delta_x, delta_y];
        end
        
        function scale(s, origin_x, origin_y, scale_x,scale_y)
            added_past = 0;
            scale_x = scale_x/s.associated_image.zoom/s.associated_image.scale;
            scale_y = scale_y/s.associated_image.zoom/s.associated_image.scale;
            scale_x = exp(scale_x/500);
            scale_y = exp(scale_y/500);
            if ~isempty(s.commands_past) && strcmp(s.commands_past{end},'scale')
                last_commands = s.past_lines{end};
                if last_commands(3)==origin_x && last_commands(4)==origin_y
                    s.past_lines{end} = s.past_lines{end}.*[scale_x,scale_y,1,1];
                    added_past = 1;
                end
            end
            if ~added_past
                s.past_lines = {s.past_lines, [scale_x,scale_y,origin_x,origin_y]};
                s.commands_past = {s.commands_past, 'scale'};
            end
            s.scale_(scale_x,scale_y, origin_x, origin_y)
            s.commands_future = {};
            s.future_lines = {};            
        end
        
        function scale_(s, scale_x, scale_y, origin_x, origin_y)
            [xx,yy] = s.associated_image.convert_screen_to_image_coordinates(origin_x,origin_y);
            s.rect = s.rect - [xx, yy];
            s.rect = s.rect*[scale_x 0; 0 scale_y];
            s.rect = s.rect + [xx, yy];
        end
        
        function rotate(s, origin_x, origin_y, angle)
            added_past = 0;
            if ~isempty(s.commands_past) && strcmp(s.commands_past{end},'rotate')
                last_commands = s.past_lines{end};
                if last_commands(2)==origin_x && last_commands(3)==origin_y
                    s.past_lines{end} = s.past_lines{end} + [angle,0,0];
                    added_past = 1;
                end
            end
            if ~added_past
                s.past_lines = {s.past_lines, [angle,origin_x,origin_y]};
                s.commands_past = {s.commands_past, 'rotate'};
            end
            s.rotate_(angle, origin_x, origin_y)
            s.commands_future = {};
            s.future_lines = {};
            
%             s.last_xx = s.last_xx - delta_x;
%             s.last_yy = s.last_yy -delta_y;
%             last = [cosd(angle) -sind(angle); sind(angle) cosd(angle)]*[s.last_xx,s.last_yy];
%             s.last_xx = last(1) + delta_x;
%             s.last_yy = last(2) + delta_y;
            
        end
        
        function rotate_(s, angle, origin_x, origin_y)
            [xx,yy] = s.associated_image.convert_screen_to_image_coordinates(origin_x,origin_y);
            s.rect = s.rect - [xx, yy];
            s.rect = s.rect*[cosd(-angle) -sind(-angle); sind(-angle) cosd(-angle)];
            s.rect = s.rect + [xx, yy];
        end
        
        function reset_rect(s)
            s.past_lines = {s.past_lines, s.rect};
            s.rect = [];
            s.commands_past = {s.commands_past, 'full'};
            s.commands_future = {};
            s.future_lines = {};
        end
        
        
        function rect = set_rect(s,rect)
            s.past_lines = {s.past_lines, s.rect};
            s.rect = rect;
            s.commands_past = {s.commands_past, 'full'};
            s.commands_future = {};
            s.future_lines = {};
        end
        
        function rect = get_rect(s)
            rect = s.rect;
        end
        
        function subtract_rect(s, delete_rect) 
            s.past_lines = {s.past_lines, s.rect};
            if ~isempty(delete_rect)
                s.rect = subtract(polyshape(s.rect(:,1),s.rect(:,2)), polyshape(delete_rect(:,1),delete_rect(:,2)));
                s.rect = s.rect.Vertices;
            end
            s.rect = [s.rect;[NaN NaN]];
            s.future_lines = {};
            s.commands_future = {};
            s.commands_past = {s.commands_past, 'full'};
            
        end
        
        function update_rect(s, xx, yy)
            if isempty(s.rect) || (xx~=s.rect(end,1) && yy~=s.rect(end,2))
                s.rect = [s.rect; [xx yy]];
                s.past_lines = {s.past_lines, []};
                s.commands_past = {s.commands_past, 'one'};
                s.future_lines = {};
                s.commands_future = {};
            end
        end
        
        function undo_rect(s)
            if ~isempty(s.commands_past)
                s.commands_future = {s.commands_future,s.commands_past{end}};
                last_command = s.commands_past{end};
                if strcmp(last_command, 'full')
                    s.future_lines = {s.future_lines,s.rect};
                    s.rect = s.past_lines{end};
                end
                if strcmp(last_command, 'one')
                    s.future_lines = {s.future_lines,s.rect(end,:)};
                    s.rect = s.rect(1:end-1,:);
                end
                if strcmp(last_command, 'move')
                    s.future_lines = {s.future_lines,s.past_lines{end}};
                    s.move_(- s.past_lines{end}(1,1),- s.past_lines{end}(1,2));
                end
                if strcmp(last_command, 'rotate')
                    s.future_lines = {s.future_lines,s.past_lines{end}};
                    angle = s.past_lines{end}(1,1);
                    ox = s.past_lines{end}(1,2);
                    oy = s.past_lines{end}(1,3);
                    s.rotate_(-angle, ox,oy);
                end
                if strcmp(last_command, 'scale')
                    s.future_lines = {s.future_lines,s.past_lines{end}};
                    scale_x = s.past_lines{end}(1,1);
                    scale_y = s.past_lines{end}(1,2);
                    ox = s.past_lines{end}(1,3);
                    oy = s.past_lines{end}(1,4);
                    s.scale_(1/scale_x, 1/scale_y, ox,oy);
                end
                if length(s.commands_past)>1
                   s.commands_past= s.commands_past{1:end-1};
                   s.past_lines= s.past_lines{1:end-1};
                else
                   s.commands_past={};
                   s.past_lines= {};
                end
            end
        end
        
        function redo_rect(s)
            if ~isempty(s.commands_future)
                s.commands_past = {s.commands_past,s.commands_future{end}};
                last_command = s.commands_future{end};
                if strcmp(last_command, 'full')
                    s.past_lines = {s.past_lines,s.rect};
                    s.rect = s.future_lines{end};
                end
                if strcmp(last_command,  'one')
                    s.past_lines = {s.past_lines,[]};
                    s.rect = [s.rect;s.future_lines{end}];
                end
                if strcmp(last_command, 'move')
                    s.past_lines = {s.past_lines,s.future_lines{end}};
                    s.move_( s.future_lines{end}(1,1),s.future_lines{end}(1,2));
                end
                if strcmp(last_command,  'rotate')
                    s.past_lines = {s.past_lines,s.future_lines{end}};
                    angle = s.future_lines{end}(1,1);
                    ox = s.future_lines{end}(1,2);
                    oy = s.future_lines{end}(1,3);
                    s.rotate_(angle, ox,oy);
                end
                if strcmp(last_command,  'scale')
                    s.past_lines = {s.past_lines,s.future_lines{end}};
                    scale_x = s.future_lines{end}(1,1);
                    scale_y = s.future_lines{end}(1,2);
                    ox = s.future_lines{end}(1,3);
                    oy = s.future_lines{end}(1,4);
                    s.scale_(scale_x,scale_y, ox,oy);
                end
                if length(s.commands_future)>1
                   s.commands_future= s.commands_future{1:end-1};
                   s.future_lines= s.future_lines{1:end-1};
                else
                   s.commands_future={};
                   s.future_lines= {};
                end
            end
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
            end
            
            if s.is_inside_margins(screen_xx,screen_yy)
                switch(s.state)
                    case StatesBBox.Editing
                        cursor = 'hand';
                        if mouse_clicked
                            interacted = 1;
                            s.update_rect(xx,yy);
                        else
                            s.state = StatesBBox.Editable;
%                             s.last_xx = None();
%                             s.last_yy = None();
                        end
                    case StatesBBox.Editable
                        if mouse_clicked
                            interacted = 1;
                            s.state = StatesBBox.Editing;  
                            s.update_rect(xx,yy);
                        end
                end
            end
            interaction_map = containers.Map({'interacted','cursor'}, {interacted, cursor});
        end

    end
end