function download_mimic_files_from_list()
    % script to download only the DICOMs from the MIMIC-CXR dataset that were sampled to be used during the experiments
    struct_folders = dir('../datasets/mimic/image_lists_before_filter/*.txt');
    folder_names = cell(length(struct_folders),1);
    [folder_names{:}] = struct_folders.name;
    joined_folders = join(strcat('../datasets/mimic/image_lists_before_filter/',folder_names),' ');
    system(['cat ', joined_folders{1}, ' > ./temp_download_mimic.txt']);
    system('wget -r -c -np -nc --user ricbl --ask-password -i ./temp_download_mimic.txt --directory-prefix=../datasets/mimic/');
end