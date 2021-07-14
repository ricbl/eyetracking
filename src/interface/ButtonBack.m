classdef ButtonBack < MyButton
    properties
        skip_count;
    end
    methods
        function s = ButtonBack(mainWindow, skip_count)
            if ~exist('skip_count','var')
                skip_count = -2;
            end
            s@MyButton('Navigate screens',ButtonBack.get_rect(mainWindow), 0, 'ButtonBack', mainWindow);
            s.skip_count = skip_count;
            %s.attach_function_clicked(@(a)set_to_skip(a));
            s.attach_function_clicked(@(a)show_button_choice(a));
        end
        
       
          function unset_inactive(s)
                unset_inactive@MyButton(s);
                s.parent.get_element_by_name('ButtonChoice_ButtonChooseScreen').unset_inactive;
           end

           function set_inactive(s)
                set_inactive@MyButton(s);
                s.parent.get_element_by_name('ButtonChoice_ButtonChooseScreen').set_inactive;
           end
           
         function hide(s)
                hide@MyButton(s);
                s.parent.get_element_by_name('ButtonChoice_ButtonChooseScreen').hide;
           end

           function unhide(s)
                unhide@MyButton(s);
                s.parent.get_element_by_name('ButtonChoice_ButtonChooseScreen').unhide;
           end
           
           function set_clicked(s)
                set_clicked@MyButton(s);
                s.parent.get_element_by_name('ButtonChoice_ButtonChooseScreen').set_clicked;
           end

           function set_active(s)
                set_active@MyButton(s);
                s.parent.get_element_by_name('ButtonChoice_ButtonChooseScreen').set_active;
           end
           
    end
    
    methods(Static)
        function rect = get_rect(mainWindow)
            centerY = (mainWindow.screenRect(2)+mainWindow.screenRect(4))/2;
            rect = [10 round(centerY-20*mainWindow.fontSize/21+mainWindow.screenRect(2)+30*mainWindow.fontSize/21+20*mainWindow.fontSize/21) mainWindow.margin-10 round(centerY+20*mainWindow.fontSize/21+mainWindow.screenRect(2)+30*mainWindow.fontSize/21+20*mainWindow.fontSize/21)];
        end
    end
end

function show_button_choice(s)
    button_choice = s.parent.get_element_by_name('ButtonChoice_ButtonChooseScreen');
    if button_choice.hidden
        button_choice.unhide();
    else
        button_choice.hide();
    end
end

function set_to_skip(s)
    s.structured_output.add_message('ButtonBack', 'going_back');
    s.exit_return = ChangeScreen.SkipScreens;
    s.n_screens_to_skip = s.skip_count;
end