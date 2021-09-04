% list_name = 'image_paths_experiments_1.txt';
% images_to_exclude = [36 120 182 280 407 464 516 331 600];
% list_name = 'image_paths_experiments_2.txt';
% images_to_exclude = [94,196,198,216,235,428,461,510,581,596,600,641,640];
% list_name = 'image_paths_experiments_4.txt';
% % [23,26,74]
% images_to_exclude = [115,147,257,287,322,326,363,420,443,516,581];
% list_name = 'image_paths_experiments_3.txt';
% images_to_exclude = [5,83,262,375,486,516,549,615];

list_name = 'image_paths_experiments_5.txt';
images_to_exclude = [1,54,74,96,106,110,112,150,159,275,295,319,352,353,380,396,480,544,549,560,579,648];
filenames = readtable(['datasets/mimic/image_lists_before_filter/' list_name],'ReadVariableNames',false, 'Delimiter', ',');
filenames(images_to_exclude,:) = [];
writetable(filenames,['datasets/mimic/image_lists/' list_name],'WriteVariableNames',0)
