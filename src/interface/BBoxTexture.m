classdef BBoxTexture < handle
    properties
       texture_changed_last_update; 
       texture_index;
       mainWindow;
    end
   methods
       function s = BBoxTexture(mainWindow)
           s.mainWindow = mainWindow;
           s.texture_index = Screen('MakeTexture', mainWindow.winMain,zeros(mainWindow.screenRect(4)-mainWindow.screenRect(2), mainWindow.screenRect(3)-mainWindow.screenRect(1)-2*mainWindow.margin ,4)); 
           Screen('BlendFunction', s.texture_index, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
           s.texture_changed_last_update = 0;
       end
        
         function reset_texture(s)
             [sourceFactorOld, destinationFactorOld, colorMaskOld] = Screen('BlendFunction', s.texture_index, GL_ONE, GL_ZERO); 
             Screen('FillRect',s.texture_index,[0 0 0 0], []);
            Screen('BlendFunction', s.texture_index, sourceFactorOld, destinationFactorOld, colorMaskOld); 
         end
   end
end