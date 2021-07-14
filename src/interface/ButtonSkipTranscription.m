classdef ButtonSkipTranscription < MyButton
    methods
        function s = ButtonSkipTranscription(mainWindow)
            s@MyButton('Skip editting',ButtonSkipTranscription.get_rect(mainWindow), 0, 'ButtonSkipTranscription', mainWindow);
            s.attach_function_clicked(@(a)set_to_skip(a));
        end
    end
    
    methods(Static)
        function rect = get_rect(mainWindow)
            centerY = (mainWindow.screenRect(4)-mainWindow.screenRect(2)-10-20*mainWindow.fontSize/21);
            rect = [10 round(centerY-20*mainWindow.fontSize/21) mainWindow.margin-10 round(centerY+20*mainWindow.fontSize/21)];
        end
    end
end

function set_to_skip(s)
    s.structured_output.add_message('ButtonSkipTranscription', 'skip_transcription');
    s.exit_return = ChangeScreen.SkipScreens;
    s.n_screens_to_skip = 2;
end