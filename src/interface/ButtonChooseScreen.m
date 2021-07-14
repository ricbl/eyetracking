classdef ButtonChooseScreen < ButtonChoice

    methods
        function s = ButtonChooseScreen(mainWindow)
            centerY = (mainWindow.screenRect(2)+mainWindow.screenRect(4))/2;
            start_y = round(centerY+20*mainWindow.fontSize/21+mainWindow.screenRect(2)+30*mainWindow.fontSize/21+20*mainWindow.fontSize/21+5*mainWindow.fontSize/21);
            end_y = round(centerY+90*mainWindow.fontSize/21-mainWindow.screenRect(2)+175*mainWindow.fontSize/21);
            delta_y = floor((end_y-start_y)/6);
            s@ButtonChoice(mainWindow,mainWindow.choices_choose_screen,'ButtonChooseScreen',[10 start_y mainWindow.margin-10 delta_y+start_y], 1, 0, 1, 0, 0, zeros( 1,length(mainWindow.choices_choose_screen) ), 0);
            s.hide();
            
            s.attach_function_clicked(@(a)set_to_skip(a));
            
        end
    end
end
    
function set_to_skip(s)
    chosen = s.parent.get_element_by_name('ButtonChoice_ButtonChooseScreen').get_chosen;
    s.n_screens_to_skip = s.mainWindow.choices_choose_screen_index{find(chosen)} - s.mainWindow.screen_i;
    s.structured_output.add_message('ButtonChooseScreen', 'going_back', s.n_screens_to_skip);
    s.exit_return = ChangeScreen.SkipScreens;
end