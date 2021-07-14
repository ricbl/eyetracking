classdef ButtonNextOther < ButtonNext
    methods
        function s = ButtonNextOther(mainWindow, single_choice_list)
            s@ButtonNext(mainWindow, 1);
            s.attach_function_clicked(@(a)set_to_skip(a,single_choice_list));
        end
    end
end

function set_to_skip(s, single_choice_list)
    chosen = s.parent.get_element_by_name('ButtonChoice_disease').get_chosen();
    if ~chosen(end)
        s.exit_return = ChangeScreen.SkipScreens;
        s.n_screens_to_skip = 2;
    else
        s.exit_return = ChangeScreen.SkipScreens;
        s.n_screens_to_skip = 1;
        return;
    end
    if s.mainWindow.skip_box_screen.get_skip_box_screen(chosen, single_choice_list)   
        s.exit_return = ChangeScreen.SkipScreens;
        s.n_screens_to_skip = 4;
    end
end