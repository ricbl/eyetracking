classdef MyButton < InteractiveTemplate
   properties
       x_max;
       x_min;
       y_max;
       y_min;
       rect;
       text;
       state;
       canHoldClicked;
       color_button;
       exit_return;
       functions_clicked;
       text_previous_update;
       mouse_button_index;
       n_screens_to_skip;
       texture_mode;
       texture;
       accept_space;
       space_pressed;
       space_initialized;
       time_ignore_movement_in_days;
       time_became_active;
   end
   methods
       function s = MyButton(text, rect, canHoldClicked, name, mainWindow, accept_space)
           s@InteractiveTemplate(Depths.button_depth, name, mainWindow, 0);
           s.texture = None();
           s.time_ignore_movement_in_days = 200/1000/60/60/24;
           s.time_became_active = now;
           s.y_max = rect(4);
           s.y_min = rect(2); 
           s.x_max = rect(3);
           s.x_min = rect(1);
           s.text = text;
           s.texture = None();
           s.text_previous_update = '';
           s.rect = rect;
           s.canHoldClicked = canHoldClicked;
           s.color_button = None();
           s.state = StatesMyButton.Active;
           s.exit_return = ChangeScreen.No;
           s.functions_clicked = {};
           s.mouse_button_index = 1;
           s.n_screens_to_skip = 1;
           s.texture_mode = 1;
           if ~exist('accept_space','var')
               s.accept_space = 0;
           else
               s.accept_space = accept_space;
           end
           s.space_pressed = 0;
           s.space_initialized = 0;
           s.update_texture;
       end
       
       function update_texture(s)
           if s.texture_mode == 1
               if ~None.isNone(s.texture)
                    Screen('Close',s.texture)
               end
               s.texture = Screen('MakeTexture', s.mainWindow.winMain, zeros(1*(s.rect(4)-s.rect(2)), 1*(s.rect(3)-s.rect(1)),4), 0, 0, 1);
               Screen('TextFont',s.texture,s.mainWindow.fontName);
                Screen('TextSize',s.texture,floor(min([((s.x_max-s.x_min)*0.95/length(s.text)/s.mainWindow.character_width),1])*s.mainWindow.fontSize));
              s.draw_texture(s.texture, 1*(s.rect-[s.rect(1) s.rect(2) s.rect(1) s.rect(2)]));
           end
       end
       
       function set_texture_mode(s, mode)
           s.texture_mode = mode;
       end
       
       function action_clicked(s)
           for ii = 1:length(s.functions_clicked)
               s.functions_clicked{ii}(s);
           end
       end
       
       function attach_function_clicked(s, fn)
           s.functions_clicked{end+1} = fn;
       end
       
      function unset_inactive(s)
         switch(s.state)
               case StatesMyButton.InactiveHidden
                   s.state = StatesMyButton.ActiveHidden;
               case StatesMyButton.Inactive
                   s.state = StatesMyButton.Active;
         end
       end
       
       function set_inactive(s)
         switch(s.state)
               case {StatesMyButton.Active,StatesMyButton.OutsideClickActive,StatesMyButton.ClickingActive, StatesMyButton.ClickingClicked,StatesMyButton.OutsideClickClicked,StatesMyButton.Clicked}
                   s.state = StatesMyButton.Inactive;
               case {StatesMyButton.ClickedHidden, StatesMyButton.ActiveHidden}
                   s.state = StatesMyButton.InactiveHidden;
         end
       end
       
       function set_active(s)
          switch(s.state)
               case {StatesMyButton.Clicked}
                   s.state = StatesMyButton.Active;
               case {StatesMyButton.OutsideClickClicked}
                   s.state = StatesMyButton.OutsideClickActive;
               case {StatesMyButton.ClickingClicked}
                   s.state = StatesMyButton.ActiveClicked;
               case StatesMyButton.ClickedHidden
                   s.state = StatesMyButton.ActiveHidden;
          end
       end
       
       function set_clicked(s)
           switch(s.state)
               case {StatesMyButton.Active}
                   s.state = StatesMyButton.Clicked;
               case {StatesMyButton.OutsideClickActive}
                   s.state = StatesMyButton.OutsideClickClicked;
               case {StatesMyButton.ClickingActive}
                   s.state = StatesMyButton.ClickingClicked;
               case StatesMyButton.ActiveHidden
                   s.state = StatesMyButton.ClickedHidden;
           end
       end
       
       function hide(s)
           switch(s.state)
               case StatesMyButton.Inactive
                   s.state = StatesMyButton.InactiveHidden;
               case {StatesMyButton.Active,StatesMyButton.OutsideClickActive,StatesMyButton.ClickingActive}
                   s.state = StatesMyButton.ActiveHidden;
               case {StatesMyButton.ClickingClicked,StatesMyButton.OutsideClickClicked,StatesMyButton.Clicked}
                   s.state = StatesMyButton.ClickedHidden;
           end
       end
       
      function unhide(s)
           switch(s.state)
               case StatesMyButton.ClickedHidden
                   s.state = StatesMyButton.Clicked;
               case StatesMyButton.ActiveHidden
                   s.state = StatesMyButton.Active;
               case StatesMyButton.InactiveHidden
                   s.state = StatesMyButton.Inactive;
           end
      end
       
      function update_text(s,text)
         s.text = text; 
      end
      
      function to_return = get_clicked(s)
          switch(s.state)
              case {StatesMyButton.ClickedHidden, StatesMyButton.ClickingClicked, StatesMyButton.Clicked, StatesMyButton.OutsideClickClicked}
                  to_return = 1;
              otherwise
                  to_return = 0;
          end
      end
      
       function interaction = update(s)
           changed = 0;
           previous_color_button = s.color_button;
           switch(s.state)
               case {StatesMyButton.OutsideClickActive, StatesMyButton.Active}
                   s.color_button = [0.5 0.5 0.5];
               case {StatesMyButton.OutsideClickClicked, StatesMyButton.Clicked}
                   s.color_button = [1 0.7 1];
                   if ~s.canHoldClicked
                       s.state = StatesMyButton.Active;
                       s.action_clicked;
                   end
               case {StatesMyButton.ActiveHidden,StatesMyButton.InactiveHidden,StatesMyButton.ClickedHidden}
                   s.color_button = None();
               case {StatesMyButton.Inactive}
                   s.color_button = [0.08 0.08 0.08];
               case {StatesMyButton.ClickingActive, StatesMyButton.ClickingClicked}
                   s.color_button = [0.25 0.25 0.25];
           end
            if ~isequal(previous_color_button,s.color_button)
               changed = 1; 
            end
            if ~isequal(s.text_previous_update,s.text)
               changed = 1; 
               s.update_texture;
            end
            s.text_previous_update = s.text;
            interaction = containers.Map({'changed', 'exit'}, {changed, s.exit_return});
       end
       function ishit = hit(s,x,y)
           ishit = x<s.x_max & x > s.x_min & y > s.y_min & y < s.y_max;
       end
       
       function interaction = interact(s, mouse, keyboard)
           interacted = 0;
           [mouse_clicked, mouse_changed_x, mouse_changed_y] = BufferInput.get_indexed_values(mouse, s.mouse_button_index);
           if s.accept_space
               keyboard_buffer = keyboard('buffer');
               space_pressed = keyboard_buffer(KbName('space'));
               if ~space_pressed && ~s.space_initialized
                   s.space_initialized = 1;
               end
               if s.space_initialized
                   if ~s.space_pressed 
                       if space_pressed
                           mouse_clicked = 1;
                           mouse_changed_x = (s.x_max + s.x_min) / 2;
                           mouse_changed_y = (s.y_min + s.y_max) / 2;
                           s.space_pressed = 1;
                       end
                   else
                       mouse_clicked = 0;
                       mouse_changed_x = (s.x_max + s.x_min) / 2;
                       mouse_changed_y = (s.y_min + s.y_max) / 2;
                       s.space_pressed = 0;
                   end
               end
           end
           
           if None.isNone(mouse_changed_x) || None.isNone(mouse_changed_y)
               if s.state == StatesMyButton.ClickingActive || s.state == StatesMyButton.ClickingClicked
                    interacted = 1;
               end
               interaction = containers.Map({'interacted', 'cursor'}, {interacted,''});
               return
           end
           
           switch(s.state)
               case StatesMyButton.Active
                   if mouse_clicked
                       if s.hit(mouse_changed_x,mouse_changed_y)
                           s.state = StatesMyButton.ClickingActive;
                           s.time_became_active = now;
                           interacted = 1;
                       else
                           s.state = StatesMyButton.OutsideClickActive;
                       end
                   end
               case StatesMyButton.ClickingActive
                   interacted = 1;
                   if ~mouse_clicked 
                       if s.hit(mouse_changed_x,mouse_changed_y) || now-s.time_became_active<s.time_ignore_movement_in_days   
                          s.state = StatesMyButton.Clicked;
                       else
                          s.state = StatesMyButton.Active;
                       end
                   end
               case StatesMyButton.Clicked
                   if mouse_clicked
                       if s.hit(mouse_changed_x,mouse_changed_y)
                            s.state = StatesMyButton.ClickingClicked;
                            s.time_became_active = now;
                            interacted = 1;
                       else
                            s.state = StatesMyButton.OutsideClickClicked;
                       end
                   end
               case StatesMyButton.ClickingClicked
                   interacted = 1;
                   if ~mouse_clicked
                       if s.hit(mouse_changed_x,mouse_changed_y) || now-s.time_became_active<s.time_ignore_movement_in_days  
                            s.state = StatesMyButton.Active;
                       else
                           s.state = StatesMyButton.Clicked;
                       end
                   end
               case StatesMyButton.OutsideClickClicked
                   if ~mouse_clicked
                       s.state = StatesMyButton.Clicked;
                   end
               case StatesMyButton.OutsideClickActive
                   if ~mouse_clicked
                       s.state = StatesMyButton.Active;
                   end
               
                   
           end 
           interaction = containers.Map({'interacted', 'cursor'}, {interacted,''});
       end
       
       function draw(s, cumulative_drawing)
           if ~None.isNone(s.color_button)
               cumulative_drawing.add_fill_rect(s.depth, s.color_button, s.rect);
               if s.texture_mode==0
                    cumulative_drawing.add_formatted_text(s.depth, s.text, 'center', 'center', [0 0 0], [],[],[],[],[],s.rect);
               elseif s.texture_mode==1
                   cumulative_drawing.add_texture(s.depth, s.texture,[],s.rect);
               end
           else
               cumulative_drawing.add_fill_rect(s.depth, [0 0 0], s.rect);
           end
       end
       
      function draw_texture(s, texture_text, rect)
          
           DrawFormattedText(texture_text, s.text, 'center', 'center', [0 0 0 1.25], [],[],[],[],[], rect);
      end
       
       function interaction = before_destruction(s)
           if ~None.isNone(s.texture)
                Screen('Close',s.texture);
           end
           interaction = containers.Map({'exit','n_screens_to_skip'}, {s.exit_return,s.n_screens_to_skip});
       end
   end
end