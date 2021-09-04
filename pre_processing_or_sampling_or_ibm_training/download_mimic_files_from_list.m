function download_mimic_files_from_list()
    struct_folders = dir('../../datasets/mimic/image_lists/*.txt');
    folder_names = cell(length(struct_folders),1);
    [folder_names{:}] = struct_folders.name;
    joined_folders = join(strcat('../../datasets/mimic/image_lists/',folder_names),' ');
    system(['cat ', joined_folders{1}, ' > ./temp_download_mimic.txt']);
    system('wget -r -N -c -np -nc --user ricbl --ask-password -i ./temp_download_mimic.txt --directory-prefix=../../datasets/mimic/');
end