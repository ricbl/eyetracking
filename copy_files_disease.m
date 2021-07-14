function copy_files_disease
    disease_labels= {'Atelectasis','Cardiomegaly','Consolidation','Edema','EnlargedCardiomediastinum','Fracture','LungLesion','LungOpacity','NoFinding','PleuralEffusion','PleuralOther','Pneumonia','Pneumothorax','SupportDevices'};
    for index_disease_label = 1:length(disease_labels)
        disease_label = disease_labels{index_disease_label};
        filenames = readtable(strcat('./datasets/mimic/image_lists_disease/',disease_label,'.txt'),'ReadVariableNames',false);
        
        mkdir(strcat('./datasets/mimic/image_lists_disease/',disease_label))
        for index_fn = 1:height(filenames)
            la = join(filenames(index_fn,:).Variables,'/')
            la = la{1}
            copyfile(la, strcat('./datasets/mimic/image_lists_disease/',disease_label), 'f')
        end
    end
end