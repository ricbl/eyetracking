  
function generate_image_from_saved_data(image_filename, rect_list, is_ellipsis, label_list, label_matrix, is_from_center,filepath_out, draw_labels, user, labels_present)
    labels_array = {'A','B','C', 'D', 'E', 'F','G','H','I','J','K','L','M','N','P','Q','R','S','T','U','V','W','X','Y','Z','a','b','d','e','f','g','h','m','n','q','r','t','æ','Æ','@','#','%','$','£','¥','§','Ø','β','ζ','θ','δ','λ','ξ','π','φ','ψ','Δ','Λ','Ξ','Π','Σ','Ω','©','®','¬','«','»','!','õ','ñ','Ñ','â','ê','ü','ÿ','ï'}; 
    screenRect = [0 0 3840 2160];
%     screenRect = [0 0 1920 1080];
    screenNumber = min(Screen('Screens'));
    winMain = Screen('OpenWindow', screenNumber, 0, screenRect, 32, 2);
    Screen('ColorRange', winMain, 1.0, 0, 1);
    header = dicominfo(image_filename);
    image = struct;
    max_possible_value = (2^double(header.BitDepth)-1);
    image.image = double(dicomread(image_filename))/max_possible_value;
    if header.PhotometricInterpretation=='MONOCHROME1'
        image = 1-image;
    end
    windowing_width = header.WindowWidth(1)/max_possible_value;
    windowing_level = header.WindowCenter(1)/max_possible_value;
    image_size = size(image.image);
    image_size_x = image_size(2);
    image_size_y = image_size(1);
    fontSize = round(38*1.5);
    Screen('Preference', 'SkipSyncTests', 0);
    Screen('Preference', 'VisualDebugLevel', 3);
    Screen('BlendFunction', winMain, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    fontName = 'NotoMono';
    Screen('TextFont',winMain,fontName);
    Screen('TextSize',winMain, round(fontSize*0.5));
    character_width = DrawFormattedText(winMain, 'a', 0,0, [0 0 0]);
    Screen('FillRect', winMain, [0 0 0 0]);
    
    Screen('Flip', winMain, [],1);
    Screen('Preference', 'TextRenderer', 1);
              
    
    
    margin = min([(1920 - 1080)/2, fontSize*0.6*25]);
    
    source_rect = [0 0 image_size_x image_size_y];
    available_x_picture = screenRect(3)-screenRect(1)-margin*2;
    available_y_picture = screenRect(4)-screenRect(2);
    scale = set_scale_drawing(image_size_x, image_size_y, available_x_picture, available_y_picture);
    dest_rect = [get_center_x(screenRect)-image_size_x/2*scale get_center_y(screenRect)-image_size_y/2*scale ...
                   get_center_x(screenRect)+image_size_x/2*scale get_center_y(screenRect)+image_size_y/2*scale  ];
    current_x = apply_windowing(image.image,windowing_level,windowing_width);
    current_texture_index =Screen('MakeTexture', winMain, current_x, 0,0,2);
    DrawFormattedText(winMain, user, screenRect(3)-screenRect(1)-margin+20, 50, [1 1 1 2]);
    Screen('DrawTexture', winMain, current_texture_index, source_rect, dest_rect, [], [], []);
    Screen('Flip', winMain, [],1);
    i = 1;
    for rect_old = rect_list
        rect_old = rect_old{1};
        if is_from_center
            rect = convert_coordinates_to_corner(rect_old);
        else
            rect = rect_old;
        end
        rect_ = convert_saved_rect_to_screen(rect,source_rect, dest_rect);
        rect_1 = round(rect_(1));
        rect_2 = round(rect_(2));
        rect_3 = round(rect_(3));
        rect_4 = round(rect_(4));  
        dest_rect_box = [min([rect_1 rect_3]) min([rect_2 rect_4]) max([rect_1 rect_3]) max([rect_2 rect_4])];
        if is_ellipsis
            eccentricity = (max([rect_1 rect_3])-min([rect_1 rect_3]))/(max([rect_2 rect_4])-min([rect_2 rect_4]));
            if eccentricity<1
                eccentricity = 1/eccentricity;
            end

            Screen('FrameOval', winMain, [0 1 0 0.8], ...
                dest_rect_box,...
                2/32*fontSize*eccentricity);
            Screen('Flip', winMain, [],1);
        else
            Screen('FrameRect', winMain, [0 1 0 0.8], ...
                dest_rect_box,...
                2/32*fontSize);
            Screen('Flip', winMain, [],1);
        end
        
        
        if draw_labels
            [x_label,y_label] = get_label_coordinates(rect, source_rect, dest_rect, is_ellipsis, round(fontSize*0.5));
            DrawFormattedText(winMain, labels_array{i}, x_label, y_label, [0 1 0 2]);
        end
        i = i + 1;
    end
    if draw_labels
        draw_disease_selection(fontSize, screenRect, label_list, character_width, margin, labels_array, label_matrix, winMain, labels_present);
    end
    Screen('Flip', winMain, [],1);
    screenImageArray = Screen('GetImage', winMain,[], 'backBuffer');
    Screen('Flip', winMain, [],1);
    imwrite(screenImageArray, filepath_out);
    Screen('Close', current_texture_index); 
    sca
end
    
 function draw_disease_selection(fontSize, screenRect, label_list, character_width, margin, labels_array, label_matrix, winMain, labels_present)   
    current_x = {};
    spacing_chosen = round(0.8*1.15*fontSize);
    starting_y = 10;
    startin_x = 10;
    limit_Y = screenRect(4)-screenRect(2);
    
    spacing_count = 1;
     a = size(label_matrix);
     n_labels = length(labels_present);
     n_boxes = a(2);
    sum_per_label = sum(label_matrix, 2);
    for k=1:n_labels
        color_not_selected = [0.3 0.3 0.3 1];
        color_selected = [1 0.7 1 1];
        color_past_box = [0 1 0 1];
        if labels_present(k)
            color = color_selected;
        else
            color = color_not_selected;
        end
        DrawFormattedText(winMain, label_list{k}, startin_x, starting_y+spacing_chosen*(spacing_count), color);
        width_texture_text = length(label_list{k})*floor(character_width);
        current_x{end+1} = startin_x+width_texture_text;

        for j=1:n_boxes
            if j==5
                label_matrix(k,j)
            end
            if label_matrix(k,j)>0
                if current_x{k}>=margin-1-spacing_chosen
                    spacing_count = spacing_count + 1;
                    current_x{k} = startin_x;
                end
                DrawFormattedText(winMain, labels_array{j}, current_x{k}, starting_y+spacing_chosen*(spacing_count), color_past_box);

                current_x{k} = current_x{k} + character_width;
                DrawFormattedText(winMain, num2str(label_matrix(k,j)*2-1), current_x{k}, starting_y+spacing_chosen*(spacing_count), color_past_box);
                current_x{k} = current_x{k} + 1.5*character_width;
            end
        end
        spacing_count = spacing_count + 1; 
        if starting_y+spacing_chosen*(spacing_count)>limit_Y
            break;
        end
    end
 end
         
function a = apply_windowing(x,level,width)
            a = min(max(((double(x)-level)/width+0.5),0),1);
end
        
function centerY = get_center_x(screenRect)
    centerY = (screenRect(1)+screenRect(3))/2;
end

function centerY = get_center_y(screenRect)
    centerY = (screenRect(2)+screenRect(4))/2;
end
        
function [return_x,return_y] = interpolate_2d(source_rect, dest_rect, x,y)
    x_scale = (dest_rect(3)-dest_rect(1))/(source_rect(3)-source_rect(1));
    y_scale = (dest_rect(4)-dest_rect(2))/(source_rect(4)-source_rect(2));
    return_x = x_scale*(x-source_rect(1))+dest_rect(1);
    return_y = y_scale*(y-source_rect(2))+dest_rect(2);
end                        
function [return_x, return_y] = convert_image_to_screen_coordinates(x, y, source_rect, dest_rect)
    [return_x, return_y] = interpolate_2d(source_rect, dest_rect, x,y);
end                        
function rect_ = convert_saved_rect_to_screen(rect, source_rect, dest_rect)
    [rect_1,rect_2] = convert_image_to_screen_coordinates(rect(1), rect(2),  source_rect, dest_rect);
    [rect_3,rect_4] = convert_image_to_screen_coordinates(rect(3), rect(4),  source_rect, dest_rect);
    rect_ = [rect_1, rect_2, rect_3, rect_4];
end

function scale = set_scale_drawing(image_size_x, image_size_y, available_x_picture, available_y_picture)
    scale_y = available_y_picture/image_size_y;
    scale_x =available_x_picture/image_size_x;
    if scale_y>scale_x
       scale = scale_x;
    else
       scale =  scale_y;
    end
end

function [x,y] = get_label_coordinates(rect, source_rect, dest_rect, is_ellipsis, fontSize)
    rect_ = convert_saved_rect_to_screen(rect, source_rect, dest_rect);
    rect_1 = rect_(1);
    rect_2 = rect_(2);
    rect_3 = rect_(3);
    rect_4 = rect_(4);
    if is_ellipsis
        y = round((rect_2+rect_4)/2+fontSize/2);
    else
        y = min([rect_2,rect_4])-4+fontSize;
    end
    x = min([rect_1,rect_3])+4;
end

function [x_radius,y_radius] = get_radius(rect)
    x_radius = abs(rect(3) - rect(1));
    y_radius = abs(rect(4) - rect(2));
end
        
function return_rect = convert_coordinates_to_corner(rect)
    x_center = rect(1);
    y_center = rect(2);
    [x_radius,y_radius] = get_radius(rect);
    return_rect = [x_center-x_radius y_center-y_radius ...
                x_center+x_radius y_center+y_radius];
end