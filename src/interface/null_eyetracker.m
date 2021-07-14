classdef null_eyetracker < handle
    properties
       structured_output;
       edfFile;
       count_screen;
    end
   methods
       function s = null_eyetracker(structured_output) 
           s.structured_output = structured_output;
           s.count_screen = 0;
       end
       
       function start_recording(s,messenger)
           s.structured_output.add_message(messenger,'start_eye_recording');
           s.count_screen = s.count_screen + 1;
%             s.structured_output.add_message(messenger,'edf_trial', s.count_screen);
       end
        
       function end_recording(s,messenger)
           s.structured_output.add_message(messenger,'end_eye_recording');
       end
       
       function set_eyetracker_trial(s,trial)
           s.count_screen = 0;
       end

       function save_edf(s)
       end
       
       function add_message(s,message)
       end
       
       function recalibrate(s)
       end
   end
end