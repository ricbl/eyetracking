classdef InteractiveImage < InteractiveTemplate
    properties
         maximagevalue;
         minimagevalue;
         down_level;
         down_width;
         down_x;
         down_y;
         windowing_level;
         windowing_width;
         state;
         current_x;
         button_index_contrast = 3;
         available_x_picture;
         available_y_picture;
         scale;
         current_texture_index;
         x;
         windowing_level_previous_update;
         windowing_width_previous_update;
         image_size_x;
         image_size_y;
         source_rect;
         dest_rect;
         texture_changed;
         apply_window_proxy;
         x_texture;
    end
    
    methods
        function s = InteractiveImage(mainWindow)
            s@InteractiveTemplate(Depths.image_depth, 'InteractiveImage', mainWindow,1);
            s.available_x_picture = s.mainWindow.screenRect(3)-s.mainWindow.screenRect(1)-s.mainWindow.margin*2;
            s.available_y_picture = s.mainWindow.screenRect(4)-s.mainWindow.screenRect(2);
            s.maximagevalue = 1;
            s.minimagevalue = 0;
            s.texture_changed = 1;
            s.windowing_level_previous_update=0;
            s.windowing_width_previous_update=0;
            s.reset_window();
            s.state = StatesInteractiveImage.Waiting;
            s.x = s.mainWindow.epoch_input.image;
            s.reset_window;
            s.current_x = s.x;
            s.scale = 1;
            s.current_texture_index = Screen('MakeTexture',s.mainWindow.winMain, s.x);
        end
        
        function on_instantiation(s,parent)
            on_instantiation@InteractiveTemplate(s,parent);
            image_size = size(s.x);
            s.image_size_x = image_size(2);
            s.image_size_y = image_size(1);
            s.structured_output.add_message(class(s),'image_size_x',s.image_size_x);
            s.structured_output.add_message(class(s),'image_size_y',s.image_size_y);      
            
            s.set_scale_drawing(s.x);
            s.source_rect = [0 0 s.image_size_x s.image_size_y];
            s.dest_rect = [s.mainWindow.get_center_x-s.image_size_x/2*s.scale s.mainWindow.get_center_y-s.image_size_y/2*s.scale ...
                           s.mainWindow.get_center_x+s.image_size_x/2*s.scale s.mainWindow.get_center_y+s.image_size_y/2*s.scale  ];
            s.save_rects;
            s.mainWindow.et.start_recording(class(s));
        end
        
        function save_rects(s)
            for ii = 1:4
                s.structured_output.add_message(class(s),['source_rect_dimension_',num2str(ii)],s.source_rect(ii));
                s.structured_output.add_message(class(s),['dest_rect_dimension_',num2str(ii)],s.dest_rect(ii));
            end
        end
        
        function interaction = before_destruction(s)
            s.mainWindow.et.end_recording(class(s));
            interaction = before_destruction@InteractiveTemplate(s);
            if ~None.isNone(s.current_texture_index)
               Screen('Close', s.current_texture_index); 
            end            
        end
        
        function set_scale_drawing(s,image)
            scale_y = s.available_y_picture/s.image_size_y;
            scale_x = s.available_x_picture/s.image_size_x;
            if scale_y>scale_x
               s.scale = scale_x;
            else
               s.scale =  scale_y;
            end
            s.structured_output.add_message(class(s),'set_scale',s.scale);
        end
        
        function createTexture(s,image)
            if ~None.isNone(s.current_texture_index)
                Screen('Close',s.current_texture_index)
            end
%              Screen('CopyWindow',s.x_texture,s.current_texture_index); 
             s.current_texture_index =Screen('MakeTexture', s.mainWindow.winMain, image, 0,0,2);
        end
        
        function drawTexture(s, image, cumulative_drawing)
            if s.texture_changed
                s.createTexture(image);
%                     s.createTexture(s.x);
%                     InteractiveImage.apply_windowing_2(s.current_texture_index,s.windowing_level,s.windowing_width);
                s.texture_changed = 0;
            end
            cumulative_drawing.add_texture(s.depth, s.current_texture_index, s.source_rect, s.dest_rect, [], [], []);
        end
        
        function reset(s)
            s.reset_window;
        end

        function reset_window(s)
            s.windowing_level = s.mainWindow.epoch_input.window_center;
            s.windowing_width = s.mainWindow.epoch_input.window_width;
        end
        
        function interaction = update(s)
            changed = 0;
            if s.windowing_level~=s.windowing_level_previous_update || s.windowing_width~=s.windowing_width_previous_update
                s.texture_changed = 1;
                changed = 1;
                s.current_x = InteractiveImage.apply_windowing(s.x,s.windowing_level,s.windowing_width);
                s.structured_output.add_message(class(s),'level',s.windowing_level);
                s.structured_output.add_message(class(s),'width',s.windowing_width);
            end
            s.windowing_level_previous_update = s.windowing_level;
            s.windowing_width_previous_update = s.windowing_width;
            interaction = containers.Map({'changed', 'exit'}, {changed, ChangeScreen.No});
        end
        
        function interaction = interact(s, mouse, ~)
            xx = mouse('mouse_x');
            yy = mouse('mouse_y');
            [mouse_clicked, mouse_changed_x, mouse_changed_y] = BufferInput.get_indexed_values(mouse, s.button_index_contrast);
            
            if None.isNone(mouse_changed_x)
                mouse_changed_x = xx;
            end
            
            if None.isNone(mouse_changed_y)
                mouse_changed_y = yy;
            end
            
            interacted = 0;
            switch(s.state)
                case StatesInteractiveImage.Waiting
                    if mouse_clicked
                        s.state = StatesInteractiveImage.Changing;
                        s.mouse_down_contrast(mouse_changed_x, mouse_changed_y);
                        s.mouse_down_move_contrast(xx,yy);
                    end
                case StatesInteractiveImage.Changing
                    interacted = 1;
                    if ~mouse_clicked
                        s.state = StatesInteractiveImage.Waiting;
                    else
                        s.mouse_down_move_contrast(xx,yy);
                    end
            end
            interaction = containers.Map({'interacted','cursor'}, {interacted, ''});
        end
        
        function mouse_down_contrast(s, x, y)
            s.down_level = s.windowing_level;
            s.down_width = s.windowing_width;
            s.down_x = x;
            s.down_y = y;
        end
        
        function mouse_down_move_contrast(s,x,y)
            delta_level = -(x - s.down_x)/4096;
            delta_width = (y - s.down_y)/4096*2;
            s.windowing_width = min([max([1/65536, s.down_width + delta_width]), 2*s.maximagevalue]);
            s.windowing_level = min([max([s.minimagevalue, s.down_level + delta_level]), s.maximagevalue]); 
        end
        
        function draw(s, cumulative_drawing)
            s.drawTexture(s.current_x, cumulative_drawing);
        end
        
        function [return_x, return_y] = convert_screen_to_image_coordinates(s, x, y)
            [return_x, return_y] = InteractiveImage.interpolate_2d(s.dest_rect, s.source_rect, x,y);
        end
        
        function [return_x, return_y] = convert_image_to_screen_coordinates(s, x, y)
            [return_x, return_y] = InteractiveImage.interpolate_2d(s.source_rect, s.dest_rect, x,y);
        end
    end
    methods(Static)
        function a = apply_windowing(x,level,width)
            a = min(max(((double(x)-level)/width+0.5),0),1);
        end
        
        function a = apply_lut(x,level,width)
            mu = level;
            v = 4*(mu-mu^2)/width;
            x = double(x);
            a = (1.+(x.*(1-mu)/mu./(1-x)).^(-v)).^(-1);
        end
        
        function apply_windowing_2(texture,level,width)
            [sourceFactorOld, destinationFactorOld, colorMaskOld] = Screen('BlendFunction', texture, GL_SRC_ALPHA, GL_SRC_ALPHA); 
             Screen('FillRect',texture,[-level+width*0.5 -level+width*0.5 -level+width*0.5 1/width], []);
            Screen('BlendFunction', texture, sourceFactorOld, destinationFactorOld, colorMaskOld); 
        end
        
        function [return_x,return_y] = interpolate_2d(source_rect, dest_rect, x,y)
            x_scale = (dest_rect(3)-dest_rect(1))/(source_rect(3)-source_rect(1));
            y_scale = (dest_rect(4)-dest_rect(2))/(source_rect(4)-source_rect(2));
            return_x = x_scale*(x-source_rect(1))+dest_rect(1);
            return_y = y_scale*(y-source_rect(2))+dest_rect(2);
        end
    end
end