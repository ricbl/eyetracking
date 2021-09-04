classdef ButtonNextCase < ButtonNextGeneric
    methods
        function s = ButtonNextCase(mainWindow)
            centerY = mainWindow.get_center_y();
            s@ButtonNextGeneric('Start Next Case',[mainWindow.screenRect(3)-(mainWindow.margin-10)-mainWindow.screenRect(1) centerY-100-mainWindow.screenRect(2)-150*mainWindow.fontSize/21 mainWindow.screenRect(3)-10-mainWindow.screenRect(1) centerY+100-mainWindow.screenRect(2)-150*mainWindow.fontSize/21], 0, 'ButtonNextCase', mainWindow);
        end
    end
end