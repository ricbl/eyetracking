classdef ScreenExit  < InteractiveScreen
    methods
        function s = ScreenExit(mainWindow, text_fn, ETon)
            centerY = mainWindow.get_center_y();
            button_exit = MyButton('Save And Exit',[mainWindow.screenRect(3)-(mainWindow.margin-10)-mainWindow.screenRect(1) centerY-50-mainWindow.screenRect(2)+25 mainWindow.screenRect(3)-10-mainWindow.screenRect(1) centerY+50-mainWindow.screenRect(2)+25], 0, 'ButtonSaveExit', mainWindow);
            button_exit.attach_function_clicked(@(a)set_to_exit(a));
            
            button_recalibrate = MyButton('Recalibrate',[mainWindow.screenRect(3)-(mainWindow.margin-10)-mainWindow.screenRect(1) centerY-50-mainWindow.screenRect(2)+150 mainWindow.screenRect(3)-10-mainWindow.screenRect(1) centerY+50-mainWindow.screenRect(2)+150], 0, 'ButtonRecalibrate', mainWindow);
            button_pupil = MyButton('Redo Pupil Calibration',[mainWindow.screenRect(3)-(mainWindow.margin-10)-mainWindow.screenRect(1) centerY-50-mainWindow.screenRect(2)+275 mainWindow.screenRect(3)-10-mainWindow.screenRect(1) centerY+50-mainWindow.screenRect(2)+275], 0, 'ButtonPupil', mainWindow);
            highlight_arrow = InteractiveHighlightArrow(mainWindow, [mainWindow.screenRect(3)-(mainWindow.margin-10)-mainWindow.screenRect(1)-3*mainWindow.fontSize centerY-mainWindow.screenRect(2)+150], mainWindow.total_trials_this_session==1);
            button_next = ButtonNextCase(mainWindow);
            if ~mainWindow.live_transcription_active
                skip_back = -3;
            else
                skip_back = -1;
            end
            
            elements = {highlight_arrow,button_recalibrate,button_exit, button_next, ButtonBack(mainWindow, skip_back ), ButtonChooseScreen(mainWindow), button_pupil};
            if ETon
                elements{end+1} = InteractiveWarning(mainWindow);
            end
%             elements{end+1} = InteractiveWarning(mainWindow);
            elements{end+1} = InteractiveGenericText(mainWindow, text_fn);
            s@InteractiveScreen(mainWindow, elements)
            button_recalibrate.attach_function_clicked(@(a)recalibrate(a,s));
            button_pupil.attach_function_clicked(@(a)pupil_recalibrate(a));
            button_next.attach_function_clicked(@(a)next_trial(a));
        end
    end
end

function next_trial(s)
    s.exit_return = ChangeScreen.SkipScreens;
    s.n_screens_to_skip = 3;
end

function pupil_recalibrate(s)
    s.exit_return = ChangeScreen.NextScreen;
end

function set_to_exit(s)
    s.exit_return = ChangeScreen.ExitExperiment;
end

function recalibrate(s, interactive_screen)
    s.mainWindow.structured_output.add_message('ScreenExit','recalibrate_clicked');
    s.mainWindow.et.recalibrate;
    s.mainWindow.last_case_calibration = s.mainWindow.completed_control.total_cases_completed_this_session+1;
    s.mainWindow.drift_check.reset_drift;
    Screen('FillRect', s.mainWindow.winMain, [0 0 0], []);
    interactive_screen.cumulative_drawing.frame_to_draw_all = 1;
end