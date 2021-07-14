function xray_et
    !numlockx on
    %get input
    prompt={'User identifier','Dataset identifier (3 numbers)' 'ET on? 1 if yes', 'Continue from last finished case? 1 if yes', 'Starting case', 'Total cases completed', 'Perform live transcription', 'Time for pupil', 'Dataset name', 'BBox from center', 'Skip instruction screens', 'Skip chest box', 'Record Videos'};
     def={'test','204','0','1', '1', '0', '0','1','mimic', '0', '0','0','0'};
%     def={'user1','306','1','1', '1', '0', '3','15','mimic', '0', '0','0','0'};
%     def={'user2','307','1','1', '1', '0', '3','15','mimic', '0', '1','0','0'};
%     def={'user3','308','1','1', '1', '0', '3','15','mimic', '0', '0','0','0'};
%     def={'user4','309','1','1', '1', '0', '3','15','mimic', '0', '0','0','0'};
%     def={'user5','310','1','1', '1', '0', '3','15','mimic', '1', '0','0','0'};

    userinput=inputdlg(prompt,'Input variables',1,def,'on');
    
    user_name = userinput{1,1};
    experiment_name = userinput{2,1};
    ETon = str2double(userinput{3,1});
    load_last = str2double(userinput{4,1});
    starting_case = str2double(userinput{5,1});
    total_cases_completed = str2double(userinput{6,1});
    live_transcription_active = str2double(userinput{7,1});
    time_pupil = str2double(userinput{8,1});
    dataset_name = userinput{9,1};
    bbox_from_center = str2double(userinput{10,1});
    skip_instruction_screens = str2double(userinput{11,1});
    skip_chest_box = str2double(userinput{12,1});
    record_video = str2double(userinput{13,1});
    %bbox_from_center = 1;
    if strcmp(experiment_name(1),'2')
        skip_count = 0;
    else
        skip_count = 1;
    end
    ellipse_box = 1;
    experiments_dir = '../../experiments/';
    
    if ellipse_box
        shape_bbox = ShapesBBox.Ellipse;
    else
        shape_bbox = ShapesBBox.Rectangle;
    end
    timestamp = strcat(datestr(datetime('now'), "YYYYmmdd-HHMMSS"), '-', int2str(randi([1000,9999])));
    runDir = char(strcat(experiments_dir, user_name, '_', experiment_name, "_",timestamp));
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
    
    pupil_seconds = time_pupil;
    %labels_list = {'Normal radiograph','Atelectasis', 'Consolidation', 'Pulmonary Edema', 'Airway Wall Thickening', 'Groundglass Opacity', 'Mass', 'Nodule', 'Pneumothorax','Pleural Effusion', 'Pleural Thickening', 'Emphysema', 'Fibrosis','Wide Mediastinum', 'Enlarged Cardiac Silhouette', 'Support devices', 'Fracture', 'Quality Issue', 'Other'};
    labels_list = {'Normal radiograph','Support devices', 'Abnormal mediastinal contour', 'Enlarged cardiac silhouette', 'Enlarged hilum', 'Hiatal hernia', 'Pneumothorax', 'Pleural abnormality', 'Consolidation','Groundglass opacity','Atelectasis', 'Lung nodule or mass', 'Pulmonary edema', 'High lung volume / emphysema','Interstitial lung disease', 'Acute fracture', 'Other'};
    list_disease_required_box_if_selected = ones(1,length(labels_list)-1);
    list_disease_required_box_if_selected(find(contains(labels_list,'Support devices'))-1) = 0;
    list_disease_required_box_if_selected(find(contains(labels_list,'Other'))-1) = 0;
    %list_disease_required_box_if_selected(find(contains(labels_list,'Quality Issue'))-1) = 0;
    list_disease_forbidden_box_if_not_selected = zeros(1,length(labels_list)-1);
    single_choice_list = zeros(1,length(labels_list));
    single_choice_list(1) = 1;
    spacing_after_buttons = zeros(1,length(labels_list));
    spacing_after_buttons(find(contains(labels_list,'Normal radiograph'))) = 1;
    spacing_after_buttons(find(contains(labels_list,'Support devices'))) = 1;
    spacing_after_buttons(find(contains(labels_list,'Hiatal hernia'))) = 1;
    spacing_after_buttons(find(contains(labels_list,'Pleural abnormality'))) = 1;
    spacing_after_buttons(find(contains(labels_list,'Interstitial lung disease'))) = 1;
    spacing_after_buttons(find(contains(labels_list,'Acute fracture'))) = 1;
    
    certainty_list = {'Consistent with (>90%)', 'Suspicious for/Probably (~75%)','Possibly (~50%)','Less Likely (~25%)','Unlikely (<10%)'};
    pupil_text = @(mainWindow)['Please look at the fixation cross for the next ',num2str(pupil_seconds),' seconds.\n\nClick to continue.'];
    string_dictation = @(mainWindow)['DICTATION\n\n\n\n\nStarting case ', num2str(mainWindow.current_trial), ' of ', num2str(total_to_complete),'. \nIn the next screen, your eye movements and audio will be recorded. Dictate a report as you would in the clinical practice.\nClick to start the next case.'];
    string_label = @(mainWindow)['LABELS\n\n\n\n\nIn the next screen, select all disease labels related to the image you just saw.\nClick to go to the next screen.'];
    string_boxes = @(mainWindow)['ELLIPSES\n\n\n\n\nIn the next screen, create bounding boxes for each evidence of disease, and select which disease is associated to the box.\nClick to go to the next screen.'];
    string_chestbox = @(mainWindow)['CHESTBOX\n\n\n\n\nIn the next screen, create a bounding box for the heart and lungs.\nClick to go to the next screen.'];
    string_save = @(mainWindow)['End of case ', num2str(mainWindow.current_trial), ' of ', num2str(total_to_complete), ' cases. ',mainWindow.completed_control.get_string_cases_complete,'You are going to start another trial in the next screen. This is the time to pause, if needed.']    ;
    endString = @(mainWindow)'You have reached the end of the experiment.';
    main_window_strings_choose_screen = {'Labels','Other Label','Bounding Boxes','Chest Box','Transcription','End of Case'};
    main_window_screens_to_choose = [4,5,7,9,10,12];
    if skip_instruction_screens
        main_window_screens_to_skip = [3,6,8];
    else
        main_window_screens_to_skip = [];
    end
    if skip_chest_box
        main_window_screens_to_skip = [main_window_screens_to_skip [8,9]];
    end
    skip_box_screen = SkipBoxScreen(list_disease_forbidden_box_if_not_selected,list_disease_required_box_if_selected);
    
    main_window = MainWindow({ ...
        @(mainWindow)ScreenTextInstruction(mainWindow, pupil_text)...
        @(mainWindow)InteractiveScreen(mainWindow, {InteractivePupilCalibration(mainWindow,pupil_seconds,0)}) ...
        },{...
        @(mainWindow)ScreenTextInstruction(mainWindow,string_dictation) ...
        @(mainWindow)ScreenCollectData(mainWindow,{InteractiveDictation(mainWindow),InteractiveImageWithZoom(mainWindow), ButtonResetImage(mainWindow)}) ... %, ButtonSkipImage(mainWindow,skip_count)}) ...
        @(mainWindow)ScreenTextInstruction(mainWindow,string_label) ...
        @(mainWindow)ScreenChoice(mainWindow,labels_list, 'disease', single_choice_list, 0, 0, 1, 1,spacing_after_buttons) ...
        @(mainWindow)ScreenWriteOther(mainWindow) ...
        @(mainWindow)ScreenTextInstruction(mainWindow,string_boxes) ...
        @(mainWindow)ScreenBBoxCollection(mainWindow,certainty_list, shape_bbox, bbox_from_center, list_disease_required_box_if_selected, list_disease_forbidden_box_if_not_selected, spacing_after_buttons) ...
        @(mainWindow)ScreenTextInstruction(mainWindow,string_chestbox) ...
        @(mainWindow)ScreenChestBox(mainWindow) ...,
        @(mainWindow)ScreenWait(mainWindow) ...,
        @(mainWindow)ScreenTranscriptionEditing(mainWindow) ...,
        @(mainWindow)ScreenExit(mainWindow,string_save, ETon) ...
        @(mainWindow)ScreenTextInstruction(mainWindow, pupil_text)...
        @(mainWindow)InteractiveScreen(mainWindow, {InteractivePupilCalibration(mainWindow,pupil_seconds,1)}) ...
        },{...
        @(mainWindow)ScreenTextInstruction(mainWindow,endString)
        },...
        structured_output, live_transcription_active, main_window_strings_choose_screen, main_window_screens_to_choose, main_window_screens_to_skip, skip_box_screen, record_video);


    if ETon == 1
        EyelinkInit(0);
        el = EyelinkInitDefaults(main_window.winMain);
        et = eyetracker2(el, runDir, structured_output, main_window);
    else
        et = null_eyetracker(structured_output);
    end
    structured_output.add_et(et);
    
    structured_output.add_message('xray_et','ETon',ETon);
    structured_output.add_message('xray_et','experiment_name',experiment_name);
    structured_output.add_message('xray_et','timestamp',timestamp);
    structured_output.add_message('xray_et','runDir',runDir);
    structured_output.add_message('xray_et','numTrials',numTrials);
    structured_output.add_message('xray_et','pupil_seconds',pupil_seconds);
    structured_output.add_message('xray_et','dataset',dataset);
    joined_labels = join(labels_list, '@$');
    structured_output.add_message('xray_et','labels_list',joined_labels{1});
    if load_last && ~strcmp(user_name,'test')
        save_table = readtable('../../save_file.csv');
        save_table = save_table(save_table.experiment==str2num(experiment_name),:);
        save_table = save_table(strcmp(save_table.user,user_name),:);
        if ~isempty(save_table.last_trial)
            [~, max_starting_trial_index] = max(save_table.last_trial);
            starting_trial = save_table.last_trial(max_starting_trial_index)+1;
            total_cases_completed = save_table.total_completed_cases(max_starting_trial_index);
        else
            starting_trial = starting_case;
        end
        
    else
        starting_trial = starting_case;
    end
    completed_control = CompletedControl(total_cases_completed, total_to_complete+15);
    drift_check = DriftCheck();
    main_window.set_eye_tracker(et);
    
    cleanup = onCleanup(@()do_cleanup(structured_output, et, runDir, user_name, experiment_name,completed_control));
    
    main_window.set_completed_control(completed_control);
    main_window.set_drift_check(drift_check);
    main_window.initialize();
    save_files(structured_output, et, runDir, user_name, experiment_name,0,completed_control);
    for trial = starting_trial:numTrials
        et.set_eyetracker_trial(trial);
        structured_output.current_trial = trial;
        structured_output.current_screen = 0;
        x = image_data.next(trial);
        exit = main_window.next_trial(x, trial);
%         completed_control.case_completed;
        structured_output.add_message('CompletedControl', 'total_completed_cases', completed_control.total_cases_completed);
        save_files(structured_output, et, runDir, user_name, experiment_name,trial,completed_control);
        if exit || completed_control.all_completed
            break;
        end
    end
    structured_output.current_trial = numTrials + 1;
    structured_output.current_screen = 0;
    main_window.finalize();
    close_everything;
end

function do_cleanup(structured_output, et, runDir, user_name, experiment_name,completed_control)
    save_files(structured_output, et, runDir, user_name, experiment_name,0,completed_control);
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
    status = Eyelink('IsConnected');
    if status == 1
        Eyelink('ShutDown');
    end
end

function appendtable(str_cells, filename)
    timestamp = datenum(datetime('now'));
    fid = fopen(filename,'a');
    fprintf(fid,'%s,%s,%s,%s,%s, %s\n',str_cells{:},sprintf('%.15f', timestamp));
    fclose(fid);
end

function save_index(user_name, experiment_name, runDir, trial, completed_trials)
    appendtable({user_name, experiment_name, runDir, num2str(trial), num2str(completed_trials)}, '../../save_file.csv');    
end

function save_files(structured_output, et, runDir, user_name, experiment_name, trial, completed_control)
    status = Eyelink('IsConnected');
    if status == 1
        et.save_edf;
    end
    structured_output.save();
    save_index(user_name, experiment_name, runDir, trial, completed_control.total_cases_completed);
end