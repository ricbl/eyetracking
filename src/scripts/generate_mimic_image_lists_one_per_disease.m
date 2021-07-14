function generate_mimic_image_lists_one_per_disease
    disease_labels= {'Atelectasis','Cardiomegaly','Consolidation','Edema','EnlargedCardiomediastinum','Fracture','LungLesion','LungOpacity','NoFinding','PleuralEffusion','PleuralOther','Pneumonia','Pneumothorax','SupportDevices'};
    for index_disease_label = 1:length(disease_labels)
        
        disease_label = disease_labels{index_disease_label};
        disease_label
        filepath_metadata = '../../datasets/mimic/tables/mimic-cxr-2.0.0-metadata.csv';
        filepath_labels = '../../datasets/mimic/tables/mimic-cxr-2.0.0-chexpert.csv';
        filepath_images_filepaths = '../../datasets/mimic/tables/cxr-record-list.csv';
        filepath_splits = '../../datasets/mimic/tables/mimic-cxr-2.0.0-split.csv';
        name_lists = {''};
        n_lists = [1];
        n_images = [5];

        files_include = {'../../datasets/mimic/image_lists/image_paths_preexperiment_1.txt',...
            '../../datasets/mimic/image_lists/image_paths_preexperiment_2.txt', ...
            '../../datasets/mimic/image_lists/image_paths_preexperiment_40.txt', ...
            '../../datasets/mimic/image_lists/image_paths_preexperiment_39.txt',...
            '../../datasets/mimic/image_lists/image_paths_preexperiment_38.txt',...
            '../../datasets/mimic/image_lists/image_paths_preexperiment_37.txt',...
            '../../datasets/mimic/image_lists/image_paths_preexperiment_36.txt',...
            '../../datasets/mimic/image_lists/image_paths_preexperiment_35.txt',...
            '../../datasets/mimic/image_lists/image_paths_preexperiment_34.txt',...
            '../../datasets/mimic/image_lists/image_paths_preexperiment_33.txt',...
            '../../datasets/mimic/image_lists/image_paths_preexperiment_32.txt',...
            '../../datasets/mimic/image_lists/image_paths_preexperiment_31.txt'};
        include_study_ids = [];
        for index_file_include = 1:length(files_include)
            this_study_ids = readtable(files_include{index_file_include},'ReadVariableNames',false);
            this_study_ids = this_study_ids.('Var8');
            include_study_ids = [include_study_ids; cell2mat(cellfun(@(x) str2num(x(2:end)), this_study_ids, 'un', 0))];
        end

        metadata = readtable(filepath_metadata);
        %by subject?
        %by train/test
        %subject_list = unique(metadata.('subject_id'));
        study_list = metadata.('study_id');
        filepaths = readtable(filepath_images_filepaths);
        splits = readtable(filepath_splits);
        sum(strcmp(splits.('split'),'train'))/height(splits);

        labels = readtable(filepath_labels);

        metadata = join(metadata, filepaths);
        metadata = join(metadata, splits);

        % 15 images/8 studies are not present in the labels
        metadata = innerjoin(metadata, labels);
        metadata_filtered_positions = metadata(strcmp(metadata.('ViewPosition'),'PA') | strcmp(metadata.('ViewPosition'),'AP'),:);
        metadata_filtered_positions = metadata_filtered_positions(metadata_filtered_positions.(disease_label)==1,:);

        [group, id] = findgroups(metadata_filtered_positions.('study_id'));
        func = @(q) [length(q)];
        result = splitapply(func, metadata_filtered_positions.('ViewPosition'), group);
        counts_images_per_study = array2table([id, result],...
            'VariableNames', {'study_id','count_images'});
        metadata_filtered_positions = innerjoin(metadata_filtered_positions, counts_images_per_study);
        %remove studies with more than one frontal image(usually means that at
        %least one image is of poor quality)
        metadata_filtered_positions = metadata_filtered_positions(metadata_filtered_positions.('count_images')==1,:);
        metadata_filtered_positions = metadata_filtered_positions(ismember(metadata_filtered_positions.('study_id'),include_study_ids),:);
        metadata_filtered_positions = metadata_filtered_positions(strcmp(metadata_filtered_positions.('split'),'train') | strcmp(metadata_filtered_positions.('split'),'validate'),:);
        %result = rowfun(@percentage_labels, metadata_filtered_positions, 'GroupingVariable', 'subject_id', 'NumOutputs', 1, 'OutputVariableNames', {'averages'});
        %size(result.('averages'))
        %mean(result.('averages'),1)
        original_rng_sate = rng('default');
        rng(1);
        randomized_indices = randperm(height(metadata_filtered_positions));
        rng(original_rng_sate);
        current_paths_index = 1;
        for current_list_type = 1:length(name_lists)
            for local_list_index = 1:n_lists(current_list_type)
                 selected_paths =  metadata_filtered_positions(randomized_indices(current_paths_index:current_paths_index+n_images(current_list_type)),:).('path');
                 metadata_filtered_positions(randomized_indices(current_paths_index:current_paths_index+n_images(current_list_type)),:).('split')
                 train_p = sum(strcmp(metadata_filtered_positions(randomized_indices(current_paths_index:current_paths_index+n_images(current_list_type)),:).('split'),'train'))/length(selected_paths);
                 writecell(strcat('~/Documents/projects/eyetracking/datasets/mimic/physionet.org/files/mimic-cxr/2.0.0/',selected_paths),strcat('../../datasets/mimic/image_lists_disease/',disease_label,'.txt'));
                 current_paths_index = current_paths_index+n_images(current_list_type);
            end
        end
        %learning set is chosen with specific hard diseases in mid
        %'learning'
    end
end