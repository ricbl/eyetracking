function test_mouse_click_time
    time_start = GetSecs;
    previous_button = 0;
    start_timer = GetSecs;
    while GetSecs - time_start < 10
        [mouse_x, mouse_y, mouse_buttons] = GetMouse();
%         if mouse_buttons(1) && ~previous_button
%             GetSecs - start_timer
%         end
%         if ~mouse_buttons(1) && previous_button
%             start_timer = GetSecs;
%         end
%         previous_button = mouse_buttons(1);
        
        if ~mouse_buttons(1) && previous_button
            GetSecs - start_timer
        end
        if mouse_buttons(1) && ~previous_button
            start_timer = GetSecs;
        end
        previous_button = mouse_buttons(1);
end            
