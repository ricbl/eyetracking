function generate_mimic_image_lists_per_user
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
    %by subject?
    %by train/test
    %subject_list = unique(metadata.('subject_id'));
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
    %result = rowfun(@percentage_labels, metadata_filtered_positions, 'GroupingVariable', 'subject_id', 'NumOutputs', 1, 'OutputVariableNames', {'averages'});
    %size(result.('averages'))
    %mean(result.('averages'),1)
    
    %separating between train and test to be able to sample 80% train and
    %20% test (the MIMIC dataset originally has 97% train and 3% test)
    metadata_filtered_positions_train = metadata_filtered_positions(strcmp(metadata_filtered_positions.('split'),'train') | strcmp(metadata_filtered_positions.('split'),'validate'),:);
    metadata_filtered_positions_test = metadata_filtered_positions(strcmp(metadata_filtered_positions.('split'),'test'),:);
    
    original_rng_sate = rng('default');
    rng(1);
    randomized_indices_train = randperm(height(metadata_filtered_positions_train));
    randomized_indices_test = randperm(height(metadata_filtered_positions_test));
    current_paths_index_train = 1;
    current_paths_index_test = 1;
    for current_list_type = 1:length(name_lists)
        for local_list_index = 1:n_lists(current_list_type)
            selected_paths = {};
            for local_image_index = 1:n_images(current_list_type)
                if rand()<0.8
                    selected_paths{local_image_index} =  metadata_filtered_positions_train(randomized_indices_train(current_paths_index_train:current_paths_index_train),:).('path'){1};
                   current_paths_index_train = current_paths_index_train+1; 
                else
                    selected_paths{local_image_index} =  metadata_filtered_positions_test(randomized_indices_test(current_paths_index_test:current_paths_index_test),:).('path'){1};
                    current_paths_index_test = current_paths_index_test+1;
                end
            end
            writecell(strcat('physionet.org/files/mimic-cxr/2.0.0/',selected_paths'),strcat('../../datasets/mimic/image_lists_4/image_paths_',name_lists{current_list_type},'_',num2str(local_list_index),'.txt'));
        end
    end
    rng(original_rng_sate);
    %learning set is chosen with specific hard diseases in mid
    %'learning'
    
    for local_list_index = 2:3
        selected_paths = {};
        for local_image_index = 1:10
            exit_ = false;
            while ~exit_
                exit_ = false;
                this_row = metadata_filtered_positions_train(randomized_indices_train(current_paths_index_train:current_paths_index_train),:);
                if ~(this_row.('NoFinding')==1)
                    labels_check = {'Atelectasis','Cardiomegaly','Consolidation','Edema','EnlargedCardiomediastinum','LungLesion','LungOpacity','PleuralEffusion','PleuralOther','Pneumonia','Pneumothorax'};
                    for label_index = 1:length(labels_check)
                        if this_row.(labels_check{label_index})==1
                            exit_=true;
                        end
                    end
                end
                current_paths_index_train = current_paths_index_train+1; 
            end
            selected_paths{local_image_index} =  this_row.('path'){1};
        end
        writecell(strcat('physionet.org/files/mimic-cxr/2.0.0/',selected_paths),strcat('../../datasets/mimic/image_lists_4/image_paths_learning_',num2str(local_list_index),'.txt'));
    end
end

% 
% function lp = percentage_labels(varargin)
%      labels_table = cell(14,1);
%     [labels_table{:}] = varargin{14:27};
%     %metadata_filtered_positions.Properties.VariableNames
%     labels = {'Atelectasis','Cardiomegaly','Consolidation','Edema','EnlargedCardiomediastinum','Fracture','LungLesion','LungOpacity','NoFinding','PleuralEffusion','PleuralOther','Pneumonia','Pneumothorax','SupportDevices'};
%     lp = [];
%     for i=1:length(labels)
%         lp(end+1) = sum(labels_table{i}==1)/length(labels_table{i});
%     end
% end

function lp = percentage_labels(metadata_filtered_positions)
    %metadata_filtered_positions.Properties.VariableNames
    labels = {'Atelectasis','Cardiomegaly','Consolidation','Edema','EnlargedCardiomediastinum','Fracture','LungLesion','LungOpacity','NoFinding','PleuralEffusion','PleuralOther','Pneumonia','Pneumothorax','SupportDevices'};
    lp = [];
    for i=1:length(labels)
        lp(end+1) = sum(metadata_filtered_positions.(labels{i})==1)/height(metadata_filtered_positions);
    end
end