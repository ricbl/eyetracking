function xray_seg
    !numlockx on
    %get input
    KbName('UnifyKeyNames');
    prompt={'Dataset identifier (3 numbers)', 'Continue from last finished case? 1 if yes', 'Starting case', 'Dataset name'};
    def={'204','1', '1', 'mimic'};
    userinput=inputdlg(prompt,'Input variables',1,def,'on');
    
    experiment_name = userinput{1,1};
    load_last = str2num(userinput{2,1});
    starting_case = str2num(userinput{3,1});
    dataset_name = userinput{4,1};
    
    experiments_dir = '../../experiments_segmentation/';
    
    timestamp = strcat(datestr(datetime('now'), "YYYYmmdd-HHMMSS"), '-', int2str(randi([1000,9999])));
    runDir = char(strcat(experiments_dir, experiment_name, '_', timestamp));
    mkdir(runDir);
    
    structured_output = StructuredOutput(runDir);
    
    numTrials = 2;
    dataset = dataset_name;
    if strcmp(dataset,'mimic')
        list_types = {'learning','preexperiment','experiments'};
        list_numTrials = [10,80,650];
        list_total_to_complete = [10,50,500];
        list_type = list_types{str2num(experiment_name(1))};
        numTrials = list_numTrials(str2num(experiment_name(1)));
        list_filepath = strcat('../../datasets/mimic/image_lists/image_paths_',list_type,'_',num2str(str2num(experiment_name(2:3))),'.txt');
        image_data = MimicLoading(numTrials, structured_output, list_filepath);
        total_to_complete = list_total_to_complete(str2num(experiment_name(1)));
    elseif strcmp(dataset,'cxr14')
        image_data = CXR14(numTrials, structured_output);
        total_to_complete = 2;
    elseif strcmp(dataset,'test')
        image_data = ImageLoading(numTrials, structured_output);
        total_to_complete = 2;
    end
    
    main_window = MainWindow({...
        },{...
        @(mainWindow)ScreenSeg(mainWindow) ...,
        },{...
        },...
        structured_output, 0, [], [], [], 0, 0);
    
    et = null_eyetracker(structured_output);
    structured_output.add_et(et);
    user_name = 'seg';
    structured_output.add_message('xray_et','experiment_name',experiment_name);
    structured_output.add_message('xray_et','timestamp',timestamp);
    structured_output.add_message('xray_et','runDir',runDir);
    structured_output.add_message('xray_et','numTrials',numTrials);
    structured_output.add_message('xray_et','dataset',dataset);
%     joined_labels = join(labels_list, '@$');
%     structured_output.add_message('xray_et','labels_list',joined_labels{1});
    if load_last
        save_table = readtable('../../save_file_segmentation.csv');
        save_table = save_table(save_table.experiment==str2num(experiment_name),:);
        save_table = save_table(strcmp(save_table.user,user_name),:);
        if ~isempty(save_table.last_trial)
            [~, max_starting_trial_index] = max(save_table.last_trial);
            starting_trial = save_table.last_trial(max_starting_trial_index)+1;
        else
            starting_trial = starting_case;
        end
        
    else
        starting_trial = starting_case;
    end
    main_window.set_eye_tracker(et);
    
    cleanup = onCleanup(@()do_cleanup(structured_output, et, runDir, user_name, experiment_name));
    
    main_window.initialize();
    save_files(structured_output, et, runDir, user_name, experiment_name,0);
    for trial = starting_trial:numTrials
        et.set_eyetracker_trial(trial);
        structured_output.current_trial = trial;
        structured_output.current_screen = 0;
        x = image_data.next(trial);
        exit = main_window.next_trial(x, trial);
        save_files(structured_output, et, runDir, user_name, experiment_name,trial);
        if exit
            break;
        end
    end
    structured_output.current_trial = numTrials + 1;
    structured_output.current_screen = 0;
    main_window.finalize();
    close_everything;
end

function do_cleanup(structured_output, et, runDir, user_name, experiment_name)
    save_files(structured_output, et, runDir, user_name, experiment_name,0);
    close_everything;
end

function close_everything
    
    KbCheck();
    Screen('CloseAll');
    sca;
    close all;
    clearvars;
    ListenChar(0);
    PsychPortAudio('Close');
end

function appendtable(str_cells, filename)
    timestamp = datenum(datetime('now'));
    fid = fopen(filename,'a');
    fprintf(fid,'%s,%s,%s,%s,%s\n',str_cells{:},sprintf('%.15f', timestamp));
    fclose(fid);
end

function save_index(user_name, experiment_name, runDir, trial)
    appendtable({user_name, experiment_name, runDir, num2str(trial)}, '../../save_file_segmentation.csv');    
end

function save_files(structured_output, et, runDir, user_name, experiment_name, trial)
    structured_output.save();
    save_index(user_name, experiment_name, runDir, trial);
end