classdef MouseInput < BufferInput
   properties
       wheelDelta;
       calls_since_last_get;
       time_last_call;
       device;
       first_check;
       valuators_last_update;
   end
   methods
       function s = MouseInput()
           s@BufferInput(3);
           s.wheelDelta = 0;
           s.calls_since_last_get = 0;
           s.time_last_call = 0;
           s.first_check = 1;
           deviceString='Virtual core pointer';%'Logitech USB Optical Mouse';%% name of the scanner trigger box
            [id,name] = GetMouseIndices;% get a list of all devices connected
            for i=1:length(name)%for each possible device
                 if strcmp(name{i},deviceString)%compare the name to the name you want
                     s.device=id(i);%grab the correct id, and exit loop
                     break;
                 end
            end
            keys=[1,2,3];
            [~,~,buttons] = GetMouse([],s.device);
            keylist=zeros(1,256);
            keylist(keys)=1;
            KbQueueCreate(s.device,keylist, 2,[],4);
            KbQueueStart(s.device);
            KbQueueFlush(s.device,3);
            s.valuators_last_update = [0,0];
       end
       
       function update(s)
           if s.first_check
              s.first_check=0;
              [~,~,~] = GetMouse([],s.device);
              [~, ~] = KbQueueCheck(s.device);
              return;
           end
           time_this_call = GetSecs;
           if time_this_call- s.time_last_call > 0.03/2
               [~,~,mouse_buttons] = GetMouse([],s.device);
               mouse_buttons = mouse_buttons(1:3);
               loop_kbeventget = 0;
               if ~loop_kbeventget
                   [~, firstpress] = KbQueueCheck(s.device);
                   mouse_buttons_queue = firstpress>0;
                   mouse_buttons_queue = mouse_buttons_queue(1:3);
                   KbQueueFlush(s.device,3);
                   mouse_buttons = mouse_buttons | mouse_buttons_queue;
                   update@BufferInput(s,mouse_buttons);
               else
                   %I could loop through kbeventsget to find the mouse
                   %position when the mouse changed state,but my guess is that
                   %there will be a performace cost bigger than the position
                   %precision gain
                   nremaining = 1;
                   [mouse_x, mouse_y, ~] = GetMouse();
                   valuators = s.valuators_last_update;
                   mouse_buttons_queue_loop=zeros(1,3);
                   coordinates_at_change = [[mouse_x, mouse_y];[mouse_x, mouse_y];[mouse_x, mouse_y]];
                   previous_time = 0;
                   while nremaining>0
                       [event,nremaining] = KbEventGet(s.device);
    %                    nremaining
                       if isempty(event)
                          continue; 
                       end
                       if event.Time - previous_time < 0
                           event.Time - previous_time
                           afab
                       end
                       previous_time = event.Time;
                       if event.Keycode==0
                           valuators = event.Valuators;
                       end
                       if event.Keycode>0 & event.Keycode<4
                           if event.Pressed
                               mouse_buttons_queue_loop(event.Keycode)=1;
                           else
                               if mouse_buttons_queue_loop(event.Keycode)
                                   continue;
                               end
                           end
                           coordinates_at_change(event.Keycode,:) = valuators;
                       end
                   end
                   s.valuators_last_update = valuators;
                   KbQueueFlush(s.device,3);
                   mouse_buttons = mouse_buttons | mouse_buttons_queue_loop;
                   update_mouse(s,mouse_buttons,coordinates_at_change);
               end
               
%                s.wheelDelta = s.wheelDelta + GetMouseWheel();
               s.calls_since_last_get = s.calls_since_last_get + 1;
               s.time_last_call = time_this_call;
           end
           
       end
       
       function to_return = get(s)
           buffer_returned = get@BufferInput(s);
           [mouse_x, mouse_y, mouse_buttons] = GetMouse();
           s.wheelDelta = GetMouseWheel();
           s.calls_since_last_get;
           to_return = [buffer_returned; containers.Map({'mouse_x', 'mouse_y', 'wheelDelta'},{mouse_x, mouse_y, s.wheelDelta})];
           s.wheelDelta = 0;
           s.calls_since_last_get = 0;
           
       end
   end
end