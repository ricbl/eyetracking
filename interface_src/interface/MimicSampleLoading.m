classdef MimicSampleLoading  < ImageLoading
    methods  
        function image = load_image(s,filepath)
            header = dicominfo(filepath);
            s.structured_output.add_message('ImageLoading','bit_depth',double(header.BitDepth));
            image = struct;
            max_possible_value = (2^double(header.BitDepth)-1);
            
            x = dicomread(filepath);
            x = double(x)/max_possible_value;
            if isfield(header,'WindowWidth')
                windowing_width = header.WindowWidth(1)/max_possible_value;
                windowing_level = header.WindowCenter(1)/max_possible_value;
                if header.PhotometricInterpretation=='MONOCHROME1' | ~isfield(header, 'PixelIntensityRelationshipSign') | header.PixelIntensityRelationshipSign==1
                    x = 1-x;
                    windowing_level = 1 - windowing_level;
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
                        x = 1-x;
                        windowing_level = 1 - windowing_level;
                    end
                 else
                    windowing_width = 1;
                    windowing_level = 0.5; 
                    if header.PhotometricInterpretation=='MONOCHROME1' | ~isfield(header, 'PixelIntensityRelationshipSign') | header.PixelIntensityRelationshipSign==1
                        x = 1-x;
                        windowing_level = 1 - windowing_level;
                    end
                 end
            end
            image.window_width = windowing_width;
            image.window_center = windowing_level;
            image.image = x;
            s.structured_output.add_message('ImageLoading','window_width',image.window_width);
            s.structured_output.add_message('ImageLoading','window_center',image.window_center);
        end
        
        function filepath = get_file_path(s,index)
            filepath = ['../../datasets/mimic-sample/',num2str(index),'.dcm'];
        end
    end
end

function minVal = find_nearest(a, n)
    [~,idx]=min(abs(double(a)-double(n)));
    minVal=idx;
end