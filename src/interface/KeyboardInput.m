classdef KeyboardInput < BufferInput
   methods
       function s = KeyboardInput()
           s@BufferInput(256);
           ListenChar(2);
       end
       
       function update(s)
           [~, ~, keyboard, ~] = KbCheck();
           exit_keys = [KbName('e') KbName('LeftAlt')];
           if all(keyboard(exit_keys))
               Screen('CloseAll');
               sca;
           end
           update@BufferInput(s,keyboard);
       end
       
       function to_return = get(s)
           buffer_returned = get@BufferInput(s);
           char = GetCharNoWait;
           if abs(char) == 3 %if ctrl+c was clicked, come back to state of no command line input
               ListenChar(2);
           end
           to_return = [buffer_returned; containers.Map({'char'},{char})];
       end
   end
end