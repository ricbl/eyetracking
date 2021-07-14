classdef ButtonNextWriteOther < ButtonNext
    methods
        function s = ButtonNextWriteOther(mainWindow)
            s@ButtonNext(mainWindow, 0);
            s.attach_function_clicked(@(a)set_to_skip(a));
        end
    end
end

function set_to_skip(s)
    ButtonChoice_disease = s.mainWindow.get_labels('ButtonChoice_disease');
    choices_chosen = ButtonChoice_disease('chosen');
    single_choice = ButtonChoice_disease('single_choice');
    
    if s.mainWindow.skip_box_screen.get_skip_box_screen(choices_chosen, single_choice)
        s.exit_return = ChangeScreen.SkipScreens;
        s.n_screens_to_skip = 3;
    else
        s.exit_return = ChangeScreen.SkipScreens;
        s.n_screens_to_skip = 1;
    end
end