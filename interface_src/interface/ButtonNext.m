classdef ButtonNext < ButtonNextGeneric
    methods
        function s = ButtonNext(mainWindow, accept_space)
            centerY = mainWindow.get_center_y();
            s@ButtonNextGeneric('Next Screen',[10 round(centerY-20*mainWindow.fontSize/21-mainWindow.screenRect(2)) mainWindow.margin-10 round(centerY+20*mainWindow.fontSize/21-mainWindow.screenRect(2))], 0, 'ButtonNext', mainWindow, accept_space);
        end
    end
end
