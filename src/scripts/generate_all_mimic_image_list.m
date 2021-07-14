function generate_all_mimic_image_list
    filepath_metadata = '../../datasets/mimic/tables/mimic-cxr-2.0.0-metadata.csv';
    filepath_labels = '../../datasets/mimic/tables/mimic-cxr-2.0.0-chexpert.csv';
    filepath_images_filepaths = '../../datasets/mimic/tables/cxr-record-list.csv';
    filepath_splits = '../../datasets/mimic/tables/mimic-cxr-2.0.0-split.csv';
    
    %exclude files used for training that were already seen by radiologists
    files_exclude = {'../../datasets/mimic/image_lists/image_paths_learning_1.txt'};
    exclude_study_ids = [];
    for index_file_exclude = 1:length(files_exclude)
        this_study_ids = readtable(files_exclude{index_file_exclude},'ReadVariableNames',false);
        this_study_ids = this_study_ids.('Var8');
        exclude_study_ids = [exclude_study_ids; cell2mat(cellfun(@(x) str2num(x(2:end)), this_study_ids, 'un', 0))];
    end
    name_lists = {'preexperiment','experiments'};
    n_lists = [40,15];
    n_images = [80,650];
    metadata = readtable(filepath_metadata);

    study_list = metadata.('study_id');
    filepaths = readtable(filepath_images_filepaths);
    splits = readtable(filepath_splits);
    
    labels = readtable(filepath_labels);
    
    metadata = join(metadata, filepaths);
    metadata = join(metadata, splits);
    
    % 15 images/8 studies are not present in the labels, so they are
    % excluded in the next command
    metadata = innerjoin(metadata, labels);
    
    %only include frontal images
    metadata_filtered_positions = metadata(strcmp(metadata.('ViewPosition'),'PA') | strcmp(metadata.('ViewPosition'),'AP'),:);
    
    [group, id] = findgroups(metadata_filtered_positions.('study_id'));
    func = @(q) [length(q)];
    result = splitapply(func, metadata_filtered_positions.('ViewPosition'), group);
    counts_images_per_study = array2table([id, result],...
        'VariableNames', {'study_id','count_images'});
    metadata_filtered_positions = innerjoin(metadata_filtered_positions, counts_images_per_study);
    %remove studies with more than one frontal image(usually means that at
    %least one image is of poor quality)
    metadata_filtered_positions = metadata_filtered_positions(metadata_filtered_positions.('count_images')==1,:);
    metadata_filtered_positions(ismember(metadata_filtered_positions.('study_id'),exclude_study_ids),:)=[];
    
    selected_paths = {};
    for current_paths_index_train = 1:height(metadata_filtered_positions)
        selected_paths{current_paths_index_train} =  metadata_filtered_positions(current_paths_index_train:current_paths_index_train,:).('path'){1};
    end
    writecell(strcat('physionet.org/files/mimic-cxr/2.0.0/',selected_paths'),strcat('../../datasets/mimic/image_all_paths.txt'));

end