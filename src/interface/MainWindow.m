classdef MainWindow  < handle
    properties
        screenNumber;
        screenRect;
        fontSize;
        winMain;
        initialization;
        trials;
        et;
        structured_output;
        resolution;
        ending;
        margin;
        epoch_input;
        current_trial;
        labels;
        character_width;
        fontName;
        completed_control;
        live_transcription_active;
        last_transcription_id;
        last_transcription_filename;
        total_trials_this_session;
        screen_i;
        states;
        main_window_strings_choose_screen;
        main_window_screens_to_choose;
        choices_choose_screen;
        choices_choose_screen_index;
        last_case_calibration;
        main_window_screens_to_skip;
        drift_check;
        skip_box_screen;
        record_video;
    end
    methods
    
        function s = MainWindow(initialization, trials, ending, structured_output, live_transcription_active, main_window_strings_choose_screen, main_window_screens_to_choose, main_window_screens_to_skip, skip_box_screen,record_video)
            s.structured_output = structured_output;
            s.record_video = record_video;
            s.skip_box_screen = skip_box_screen;
            
            s.main_window_strings_choose_screen = main_window_strings_choose_screen;
            s.main_window_screens_to_skip = main_window_screens_to_skip;
            s.main_window_screens_to_choose = main_window_screens_to_choose;
            
            s.live_transcription_active = live_transcription_active;
            
            
            s.screenNumber = min(Screen('Screens'));
            %s.screenRect = [20 20 1920 1080];
            s.resolution = Screen('Resolution', s.screenNumber);
            s.screenRect = [0 0 s.resolution.width s.resolution.height];
%             s.screenRect = [0 0 900 600];
            screen_height = 336.22;
            s.total_trials_this_session = 0;
            s.last_case_calibration = 0;
            ratio_font = screen_height/194.261/s.resolution.height*1080;
            
%             s.margin = 330;
            s.labels = containers.Map();
            KbName('UnifyKeyNames');
            s.winMain = Screen('OpenWindow', s.screenNumber, 0, s.screenRect, 32, 2);
            Screen('ColorRange', s.winMain, 1.0, 0, 1);
            s.fontSize = round(38/ratio_font);
            
            
            s.margin = min([(s.resolution.width - s.resolution.height)/2, s.fontSize*0.6*25]);
            AssertOpenGL;
            KbCheck();
            
            % the following are DEF setup commands
            Screen('Preference', 'SkipSyncTests', 0);
            Screen('Preference', 'VisualDebugLevel', 3);
            Screen('BlendFunction', s.winMain, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
            Screen('FillRect', s.winMain, [0 0 0 0]);
            Screen('TextSize',s.winMain, s.fontSize);
            Screen('Flip', s.winMain);
            
            s.initialization = initialization;
            s.ending = ending;
            s.trials = trials;
            ShowCursor('CrossHair');
%             setenv('DYLD_LIBRARY_PATH', ['/opt/X11/lib:', getenv('DYLD_LIBRARY_PATH')]);
              Screen('Preference', 'TextRenderer', 1);
              
              %use monospaced font to be easier to calculate the size of
              %drawn texts
            s.fontName = 'NotoMono';
%             s.fontName = 'Inconsolata';
             Screen('TextFont',s.winMain,s.fontName);
             Screen('TextSize',s.winMain, s.fontSize);
             
             s.character_width = DrawFormattedText(s.winMain, 'a', 0,0, [0 0 0]);
             
             ListenChar(2);
             
        end
        
        function do_live_transcription(s, filename)
            s.last_transcription_filename = filename(1:end-4);
            s.structured_output.add_message('MainWindow','live_transcription_active',s.live_transcription_active);
            if s.live_transcription_active == 1
                script_name = 'run_convert_google.sh';
            elseif s.live_transcription_active == 2
                script_name = 'run_convert_dummy.sh';
            elseif s.live_transcription_active == 3
                script_name = 'run_convert_ibm.sh';
            end
            [~, printed_id] = system(['../scripts/',script_name,' --file_name ',s.last_transcription_filename]);
            s.last_transcription_id = strtrim(printed_id);
        end
        
        function ended = check_live_transcription_status(s)
            [~, printed_n_lines] = system(['ps -p ',s.last_transcription_id,' | wc -l']);
            printed_n_lines = strtrim(printed_n_lines);
            if printed_n_lines=='2'
                ended = 0;
            elseif printed_n_lines=='1'
                ended = 1; 
            else
                ended = 2;
                s.structured_output.add_message('MainWindow', 'error_message_transcription', printed_n_lines);
                if ~isfile([s.last_transcription_filename, '_1.0.txt'])
                    fileID = fopen([s.last_transcription_filename, '_1.0.txt'],'w');
%                     fprintf(fileID,printed_n_lines);
                    fprintf(fileID,'error');
                    fclose(fileID);
                    fileID = fopen([s.last_transcription_filename, '_1.0_trim.txt'],'w');
                    fprintf(fileID,'0\n0');
                    fclose(fileID);
                end
            end
        end
        
        function [transcription_results, trim_start] = get_live_transcription_results(s)
            transcription_results = fileread([s.last_transcription_filename, '_1.0.txt']);
            trim_start = splitlines(fileread([s.last_transcription_filename, '_1.0_trim.txt']));
            trim_start = str2num(trim_start{1});
        end
        
        function centerY = get_center_y(s)
            centerY = (s.screenRect(2)+s.screenRect(4))/2;
        end
        
        function centerY = get_center_x(s)
            centerY = (s.screenRect(1)+s.screenRect(3))/2;
        end

        function s = set_eye_tracker(s,et)
            s.et=et;
            s.structured_output.add_message('MainWindow','resolution_width',s.resolution.width);
            s.structured_output.add_message('MainWindow','resolution_height',s.resolution.height);
        end
        
        function set_completed_control(s,completed_control)    
            s.completed_control = completed_control;
        end
        
        function set_drift_check(s,drift_check)    
            s.drift_check = drift_check;
        end
        
        function initialize(s)
            exit = s.do_screen_loop(s.initialization, 'initialize');
        end
        
        function finalize(s)
            exit = s.do_screen_loop(s.ending, 'finalize');
        end
        
        function exit = next_trial(s,epoch_input, current_trial)
            s.epoch_input = epoch_input;
            s.current_trial = current_trial;

            s.total_trials_this_session = s.total_trials_this_session + 1;
            exit = s.do_screen_loop(s.trials, 'trial');
        end
        
        function add_labels(s, name, value)
            s.labels(name) = value;
        end
        
        function labels_map = get_labels(s, name)
            labels_map = s.labels(name);
        end
        
        function exit = do_screen_loop(s,screen_list, name)
            s.choices_choose_screen = {};
            s.choices_choose_screen_index = {};
            added_screens_to_choice = zeros(length(screen_list));
            s.states = containers.Map('KeyType','char','ValueType','any');
            s.structured_output.add_message('MainWindow',strcat('start_',name));
            i = 1;
            exit = 0;
            while i<=length(screen_list)
                s.screen_i = i;
                s.structured_output.current_screen = i;
                if ismember(i, s.main_window_screens_to_skip) 
                    i = i+1;
                else
                    this_state_fn = screen_list(i);
                    this_state_fn = this_state_fn{1};
                    this_state = this_state_fn(s);
                    s.structured_output.add_message('MainWindow', strcat('index_start_screen_',name), i);
                    s.structured_output.add_message('MainWindow', strcat(strcat('class_start_screen_',num2str(i))), class(this_state));
                    interaction = this_state.main_loop;
                    s.structured_output.add_message('MainWindow', strcat('end_screen_',name), i);
                    
                    [is_member,ind] = ismember(i, s.main_window_screens_to_choose);
                    if is_member
                        if ~added_screens_to_choice(ind)
                            s.choices_choose_screen{end+1} = s.main_window_strings_choose_screen{ind};
                            s.choices_choose_screen_index{end+1} = s.main_window_screens_to_choose(ind);
                            added_screens_to_choice(ind) = 1;
                        end
                    end
                    
                    switch interaction('exit')
                       case ChangeScreen.NextScreen
                          i = i+1;
                       case ChangeScreen.PreviousScreen
                          i = max([i-1,1]);
                       case ChangeScreen.ExitExperiment
                          exit = 1;
                          break;
                       case ChangeScreen.SkipScreens
                          i = i + interaction('n_screens_to_skip');
                       case ChangeScreen.NextTrial
                          i = length(screen_list)-2;
                    end                    
                end
            end
            
            s.structured_output.add_message('MainWindow',strcat('end_',name));
        end
    end
end
    
    