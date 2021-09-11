function copy_list_to_folder_for_checking
    struct_folders = dir('../datasets/mimic/image_lists_before_filter/*.txt');
    folder_names = cell(length(struct_folders),1);
    [folder_names{:}] = struct_folders.name;
    for index_folder = 1:length(folder_names)
    
        filenames = readtable(['../datasets/mimic/image_lists_before_filter/',folder_names{index_folder}],'ReadVariableNames',false);
        [~,folder_name,~] = fileparts(folder_names{index_folder}) ;
        mkdir(strcat('./images_check_rectangle/', folder_name));
        for index_fn =1:height(filenames)
            la = join(filenames(index_fn,:).Variables,'/');
            la = la{1};
            image_filename = ['../datasets/mimic/',la];

            header = dicominfo(image_filename);

            max_possible_value = (2^double(header.BitDepth)-1);
            image = dicomread(image_filename);
            image = double(image)/max_possible_value;
            if isfield(header,'WindowWidth')
                windowing_width = header.WindowWidth(1)/max_possible_value;
                windowing_level = header.WindowCenter(1)/max_possible_value;
                if header.PhotometricInterpretation=='MONOCHROME1' | ~isfield(header, 'PixelIntensityRelationshipSign') | header.PixelIntensityRelationshipSign==1
                    image = 1-image;
                end
            else
                 if isfield(header,'VOILUTSequence')
                    lut_center = double(header.VOILUTSequence.Item_1.LUTDescriptor(1)/2);
                    window_center = find_nearest(header.VOILUTSequence.Item_1.LUTData, lut_center);
                    deltas = [];
                    for i=10:30
                        deltas = [deltas (double(header.VOILUTSequence.Item_1.LUTData(window_center+i)) - double(header.VOILUTSequence.Item_1.LUTData(window_center-i)))/2/i];
                    end     
                    window_width = lut_center/mean(deltas)*2;
                    windowing_width = window_width/max_possible_value;
                    windowing_level = (window_center-1)/max_possible_value;
                    if windowing_width < 0
                        windowing_width = -windowing_width;
                        image = 1-image;
                        windowing_level = 1 - windowing_level;
                    end
                 else
                    windowing_width = 1;
                    windowing_level = 0.5; 
                    if header.PhotometricInterpretation=='MONOCHROME1' | ~isfield(header, 'PixelIntensityRelationshipSign') | header.PixelIntensityRelationshipSign==1
                        image = 1-image;
                    end
                 end
            end
            current_x = apply_windowing(image,windowing_level,windowing_width);

            imwrite(current_x, strcat('./images_check_rectangle/', folder_name, '/', num2str(index_fn),'.png'));        

        end
    end
end

function a = apply_lut(x,level,width)
            mu = level;
            v = 4*(mu-mu^2)/width;
            x = double(x);
            a = (1.+(x.*(1-mu)/mu./(1-x)).^(-v)).^(-1);
end

function a = apply_windowing(x,level,width)
            a = min(max(((double(x)-level)/width+0.5),0),1);
end