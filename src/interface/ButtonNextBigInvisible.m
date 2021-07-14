classdef ButtonNextBigInvisible < ButtonNextGeneric
    methods
        function s = ButtonNextBigInvisible(mainWindow)
            s@ButtonNextGeneric('',[0 0 mainWindow.screenRect(3)-mainWindow.screenRect(1) mainWindow.screenRect(4)-mainWindow.screenRect(2)], 0, 'ButtonNextBigInvisible', mainWindow, 1)
        end
        
        function interaction = update(s)
            update@ButtonNextGeneric(s);
           changed = 0;
            s.color_button = None();
            interaction = containers.Map({'changed', 'exit'}, {changed, s.exit_return});
        end
        
        function draw(s, cumulative_drawing)

        end
    end
end
