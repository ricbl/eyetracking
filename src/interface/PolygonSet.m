classdef PolygonSet < InteractiveTemplate
    properties
       state;
       box_id;
       texture_middle_screen;
       label_texture;
       manage_texture_redrawing;
       rect;
       delete_rect;
       associated_image;
       zoom_previous_update;
       pan_x_previous_update;
       pan_y_previous_update;
    end
    methods
        function s = PolygonSet(mainWindow, box_id, associated_image, texture_middle_screen)
            s@InteractiveTemplate(Depths.box_depth, strcat('PolygonSet_',box_id), mainWindow, 1);
            
            s.box_id = box_id;
            s.state = StatesSegment.Editing;
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
            s.rect = Polygon(mainWindow, associated_image, [1 0 0 0.3]);
            s.delete_rect = Polygon(mainWindow, associated_image, [0 1 0 0.3]);
            
        end
            
        function undo_rect(s)
            switch(s.state)
                case StatesSegment.Editing
                    s.rect.undo_rect;
                case StatesSegment.Removing
                    s.delete_rect.undo_rect;
            end
        end
        
        function redo_rect(s)
            switch(s.state)
                case StatesSegment.Editing
                    s.rect.redo_rect;
                case StatesSegment.Removing
                    s.delete_rect.redo_rect;
            end
        end
        
        function move(s, delta_x, delta_y)
            switch(s.state)
                case StatesSegment.Editing
                    s.rect.move(delta_x, delta_y);
                case StatesSegment.Removing
                    s.delete_rect.move(delta_x, delta_y);
            end
        end
        
        function rotate(s, angle,origin_x, origin_y)
            switch(s.state)
                case StatesSegment.Editing
                    s.rect.rotate(origin_x, origin_y, angle);
                case StatesSegment.Removing
                    s.delete_rect.rotate(origin_x, origin_y, angle);
            end
        end
        
        function scale(s, scale_x,scale_y,origin_x, origin_y)
            switch(s.state)
                case StatesSegment.Editing
                    s.rect.scale(origin_x, origin_y, scale_x, scale_y);
                case StatesSegment.Removing
                    s.delete_rect.scale(origin_x, origin_y, scale_x, scale_y);
            end
        end
                
        function reset(s)
            switch(s.state)
                case StatesSegment.Editing
                    s.rect.reset_rect;
                case StatesSegment.Removing
                    s.delete_rect.reset_rect;
            end
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
            rect_changed = s.rect.update();
            delete_rect_changed = s.delete_rect.update();
            if rect_changed | delete_rect_changed
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
            interaction_map = containers.Map({'changed', 'exit'}, {changed, ChangeScreen.No});
            s.reset_zoom_previous_update;
        end
        
        function interaction_map = interact(s,mouse, keyboard)
            switch(s.state)
                case StatesSegment.Editing
                    interaction_map = s.rect.interact(mouse, keyboard);
                case StatesSegment.Removing
                    interaction_map = s.delete_rect.interact(mouse, keyboard);
            end
        end
        
        function switch_color(s)
            if s.state == StatesSegment.Editing
                if ~None.isNone(s.rect.get_rect)
                    s.state = StatesSegment.Removing;
                end
            else
                if s.state == StatesSegment.Removing
                    s.state = StatesSegment.Editing;
                    s.rect.subtract_rect(s.delete_rect.get_rect);
                    s.delete_rect.reset_rect;
                end
            end
        end
        
        function [x,y] = get_label_coordinates(s,rect)
            [rows,cols] = find(rect(1:end,1:end,1));
            y = mean(rows);
            x = mean(cols);
            [x,y] = s.associated_image.convert_image_to_screen_coordinates(x,y);
        end
        
        function draw_cut_texture(s, texture, x, y, dest_rect)
            [texture_width, texture_height] = Screen('WindowSize', texture);
            if ~exist('dest_rect','var')
                dest_rect = [x y x+texture_width y+texture_height];
            end           
            dest_rect = dest_rect + [-s.mainWindow.margin 0 -s.mainWindow.margin 0];
            [texture_middle_width, texture_middle_height] = Screen('WindowSize', s.texture_middle_screen.texture_index);
             texture_limits = [0 0 texture_middle_width texture_middle_height];
            [~, residuals] = BBox.get_cut_residuals(dest_rect, texture_limits);
            source_rect = [0 0 texture_width texture_height] - residuals;
            if source_rect(3)-source_rect(1)>0 && source_rect(4)-source_rect(2)>0  s = settings;s.matlab.desktop.DisplayScaleFactor
                Screen('DrawTexture', s.texture_middle_screen.texture_index, texture, source_rect, dest_rect);
            end
        end
        
        function rect = convert_saved_rect_to_screen(s, rect)
            a= size(rect);
            for i=1:a(1)
                [rect(i,1),rect(i,2)] = s.associated_image.convert_image_to_screen_coordinates(rect(i,1),rect(i,2));
                rect(i,1) = round(rect(i,1));
                rect(i,2) = round(rect(i,2));
            end
        end  
        
        function C = split_at_nan(s,M)
            idx = all(isnan(M),2);
            idy = 1+cumsum(idx);
            idz = 1:size(M,1);
            C = accumarray(idy(~idx),idz(~idx),[],@(r){M(r,:)});
        end
    
        function draw_rect(s, color, rect, cumulative_drawing, dest_rect)
            if ~isempty(rmmissing(rect))
                rect_ = s.convert_saved_rect_to_screen(rect);
                dest_rect = [min(rmmissing(rect_(:,1))) min(rmmissing(rect_(:,2))) max(rmmissing(rect_(:,1)))+5 max(rmmissing(rect_(:,2)))+5];
                rect_limits = [s.mainWindow.margin 0 s.mainWindow.screenRect(3)-s.mainWindow.screenRect(1)-s.mainWindow.margin  s.mainWindow.screenRect(4)-s.mainWindow.screenRect(2)];
                [dest_rect, residuals] = BBox.get_cut_residuals(dest_rect, rect_limits);
                
                if dest_rect(4)>dest_rect(2) && dest_rect(3)>dest_rect(1)
                    rect_location = rect_ - [min(rmmissing(rect_(:,1))) min(rmmissing(rect_(:,2)))]+[residuals(1) residuals(2)];
                    rect_texture = s.draw_rect_texture(color, rect_location, [dest_rect(4)-dest_rect(2), dest_rect(3)-dest_rect(1),4]);
                    
                    s.draw_cut_texture(rect_texture,max([min(rect_(:,1)),rect_limits(1)]), max([min(rect_(:,2)),rect_limits(2)]));
                     Screen('Close',rect_texture); 
                end
            end
        end
        
        function rect_texture = draw_rect_texture(s, color, rect_location, texture_size)
            rect_texture = Screen('MakeTexture', s.mainWindow.winMain, zeros(texture_size));
            polys = s.split_at_nan(rect_location);
            for k=1:length(polys)
                poly_ = polys{k};
                size_rect_location = size(poly_);
                if size_rect_location(1)==1
                    Screen('DrawDots', rect_texture, [poly_(1,1), poly_(1,2)], 5);
                end
                if size_rect_location(1)==2
                   Screen('DrawLine', rect_texture, color, poly_(1,1), poly_(1,2), poly_(2,1), poly_(2,2),5);
                end
                if size_rect_location(1)>2
                    Screen('FillPoly', rect_texture ,color, poly_, 0);  
                end
            end
        end
        
        function draw(s, cumulative_drawing)
            if s.texture_middle_screen.texture_changed_last_update
                if s.manage_texture_redrawing
                    s.texture_middle_screen.reset_texture();
                end
                if ~None.isNone(s.rect.get_rect)
                    s.draw_rect(s.rect.color, s.rect.get_rect, cumulative_drawing);
                end
                
                if  s.state==StatesSegment.Removing 
                    s.draw_rect(s.delete_rect.color, s.delete_rect.get_rect, cumulative_drawing);
                end
                
            end
            if s.manage_texture_redrawing
                s.texture_middle_screen.texture_changed_last_update = 0;
                [texture_width, texture_height] = Screen('WindowSize',s.texture_middle_screen.texture_index);
                cumulative_drawing.add_texture(s.depth, s.texture_middle_screen.texture_index, [], [s.mainWindow.margin 0 s.mainWindow.margin+texture_width texture_height]);
            end
        end
        
        function imageArray = get_image_array(s)
            rect_texture = s.draw_rect_texture([1 1 1], s.rect.get_rect, [s.associated_image.image_size_y,s.associated_image.image_size_x]);
            imageArray=Screen('GetImage', rect_texture);
            Screen('Close',rect_texture); 
        end 
        
        function interaction_map = before_destruction(s)
            if ~None.isNone(s.rect) && ~isempty(s.rect.get_rect)
                % write to image
                mkdir([s.structured_output.local,'/',num2str(s.mainWindow.current_trial)]);
                image_filename = [s.structured_output.local,'/',num2str(s.mainWindow.current_trial),'/',s.box_id,'.png'];
                csv_filename = [s.structured_output.local,'/',num2str(s.mainWindow.current_trial),'/',s.box_id,'.csv'];
                imageArray = s.get_image_array();
                imwrite(imageArray, image_filename);
                writematrix(s.rect.get_rect,csv_filename);
                % get image name
                s.structured_output.add_message(s.name,['rect_image_filename_',s.box_id], image_filename);
                s.structured_output.add_message(s.name,['rect_vertices_filename_',s.box_id], image_filename);
            end
             
            if ~None.isNone(s.label_texture)
                Screen('Close',s.label_texture);
            end
            if s.manage_texture_redrawing
                Screen('Close',s.texture_middle_screen.texture_index);
            end
            if ~None.isNone(s.rect.current_rect_texture_index)
                Screen('Close',s.positive_rect.current_rect_texture_index)
            end
            if ~None.isNone(s.delete_rect.current_rect_texture_index)
                Screen('Close',s.negative_rect.current_rect_texture_index)
            end
            interaction_map = containers.Map({'exit'}, {ChangeScreen.No});
        end
    end
end