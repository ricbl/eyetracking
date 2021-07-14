function test_cursors
    step = 0;
    screenNumber = min(Screen('Screens'));
     AssertOpenGL;
    s.resolution = Screen('Resolution', screenNumber);
    screenRect = [s.resolution.width/2-500 s.resolution.height/2-500 s.resolution.width/2+500 s.resolution.height/2+500];
     windowPtr = Screen('OpenWindow', screenNumber, 0, screenRect, 32, 2);
     while step<153
         [xx,yy,buttons] = GetMouse;
         if buttons(1)==1 && previous_1==0
             step = step+1;
         end
         previous_1 = buttons(1);
         ShowCursor(step);
     end
end