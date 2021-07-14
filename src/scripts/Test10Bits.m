function Test10Bits
%     PsychImaging('PrepareConfiguration');
%     PsychImaging('AddTask', 'General', 'EnableNative10BitFramebuffer');
     screenNumber = min(Screen('Screens'));
     AssertOpenGL;
    s.resolution = Screen('Resolution', screenNumber);
    screenRect = [s.resolution.width/2-500 s.resolution.height/2-500 s.resolution.width/2+500 s.resolution.height/2+500];
     windowPtr = Screen('OpenWindow', screenNumber, 0, screenRect, 32, 2);
     PsychImaging('PrepareConfiguration');
    PsychImaging('AddTask', 'General', 'EnableNative10BitFramebuffer');
     Screen('ColorRange', windowPtr, 1.0, 0, 1);
     Screen('TextSize',windowPtr, 32);
     s.fontSize = 32;
    AssertOpenGL;
    KbCheck();
    Screen('Preference', 'SkipSyncTests', 0);
    Screen('Preference', 'VisualDebugLevel', 3);
    Screen('BlendFunction', windowPtr, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

     Screen('FillRect', windowPtr, 0);
     Screen('Flip', windowPtr);
     step = 500;
     invert = 0;
     previous_1 = 0;
     previous_3 = 0;
     contrast_step = 3;
     while step<530
         [xx,yy,buttons] = GetMouse;
         if buttons(1)==1 && previous_1==0
             step = step+1;
         end
         previous_1 = buttons(1);
         if buttons(3)==1 && previous_3==0
             invert = 1-invert;
         end
         previous_3 = buttons(3);
         
            
         %Screen('FillRect', windowPtr, [(step+(1-invert)*contrast_step)/(2^10) (step+(1-invert)*contrast_step)/(2^10) (step+(1-invert)*contrast_step)/(2^10)], [0 0 (screenRect(3)-screenRect(1))/2 (screenRect(4)-screenRect(2))]);
         %Screen('FillRect', windowPtr, [(step+(invert)*contrast_step)/(2^10) (step+(invert)*contrast_step)/(2^10) (step+(invert)*contrast_step)/(2^10)], [(screenRect(3)-screenRect(1))/2 0 (screenRect(3)-screenRect(1)) (screenRect(4)-screenRect(2))]);
         Screen('FillRect', windowPtr, [0 (step+(1-invert)*contrast_step)/(2^10) 0], [0 0 (screenRect(3)-screenRect(1))/2 (screenRect(4)-screenRect(2))]);
         Screen('FillRect', windowPtr, [0 (step+(invert)*contrast_step)/(2^10) 0], [(screenRect(3)-screenRect(1))/2 0 (screenRect(3)-screenRect(1)) (screenRect(4)-screenRect(2))]);
         DrawFormattedText(windowPtr, num2str(step), 'center', 'center', [1 1 1], 50);
         Screen('Flip', windowPtr);
     end
     Screen('CloseAll');

     endsca
     sca
     