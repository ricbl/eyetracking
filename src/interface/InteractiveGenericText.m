classdef InteractiveGenericText  < InteractiveTemplate
    properties
        text;
        drawn;
        px;
        py;
        width;
    end
    methods
        function s = InteractiveGenericText(mainWindow, text_fn, px, py, width)
            s@InteractiveTemplate(Depths.text_depth,'InteractiveGenericText', mainWindow, 1);
            if ~exist('px','var')
               px = 'center';
            end
            if ~exist('py','var')
              py = 'center';
            end
            if ~exist('width','var')
              width = 50;
            end
            s.px = px;
            s.py = py;
            s.width = width;
            s.text = text_fn(mainWindow);
            s.drawn = 0;
        end
        
        function interaction_map = update(s)
            interaction_map = containers.Map({'changed','exit'}, {~s.drawn,ChangeScreen.No});
            s.drawn = 1;
        end
        
        function draw(s, cumulative_drawing)            
            cumulative_drawing.add_formatted_text(s.depth, s.text, s.px, s.py, [1 1 1], s.width);
        end
    end
end