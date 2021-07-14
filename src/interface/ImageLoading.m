classdef ImageLoading  < handle
    properties
        image_array;
        structured_output;
    end
    methods
        function s = ImageLoading(numTrials, structured_output)
            s.structured_output = structured_output;
            s.image_array = {};
        end
        
        function image = load_image(s,filepath)
            info = imfinfo(filepath);
            s.structured_output.add_message('ImageLoading','bit_depth',info.BitDepth/3);
            image = struct;
            image.image = double(imread(filepath))/(2^(info.BitDepth/3)-1);
            image.window_width = 1;
            image.window_center = 0.5;
        end
        
        function filepath = get_file_path(s,index)
            filepath = ['../../datasets/test/',num2str(index),'.png'];
        end
        
        function image_return = next(s,current_index)
            s.structured_output.add_message('ImageLoading','current_index',current_index);
            s.structured_output.add_message('ImageLoading','filepath',s.get_file_path(current_index));
            image_return = s.load_image( s.get_file_path(current_index));
        end  
    end
end