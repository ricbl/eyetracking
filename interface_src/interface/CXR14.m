classdef CXR14  < ImageLoading
    methods        
        function image = load_image(s,filepath)
            image = struct;
            image.image = double(imread(filepath))/255;
            image.window_width = 1;
            image.window_center = 0.5;
        end
        
        function filepath = get_file_path(s,index)
            filepath = ['../../datasets/c14/',num2str(index),'.png'];
        end
    end
end