classdef TextBox < InteractiveTemplate
    properties
       text; 
       rect;
       block_height;
       block_width;
       line_width_in_blocks;
       text_past;
       text_future;
       clipboard;
       cursor_index_0;
       cursor_index_1;
       state;
       cursor_drawing_time_count;
       time_cursor_cycle_in_days;
       button_index_cursor;
       new_char;
       draw_cursor;
       text_directing;
       previous_cursor_index_0;
       previous_cursor_index_1;
       first_delay_keys_in_days;
       sequence_delay_keys_in_days;
       arrow_keys_state;
       arrow_keys_names;
       arrow_keys_timers;
       button_paste;
       first_text;
       cursor_index_0_past;
       cursor_index_0_future;
       cursor_index_1_past;
       cursor_index_1_future;
       characters_textures;
       line_spacing;
       blocks_sizes;
       max_block_size;
       blocks_textures;
       action_past;
       action_future;
       insert_index_past;
       insert_index_future;
       line_sizes;
       accumulated_line_sizes;
       drawing_line_sizes;
       doubleclick_in_days;
       doubleclick_minimum_in_days;
       last_click_doubleclick;
    end
    methods
        function s = TextBox(mainWindow,rect, text)
           s@InteractiveTemplate(Depths.text_depth, 'TextBox',mainWindow, 1);
           s.rect = rect;
           s.block_height = s.mainWindow.fontSize;
           s.line_spacing = ceil(s.block_height*0.3);
           s.block_width = s.mainWindow.character_width;
           s.line_width_in_blocks = floor((s.rect(3)-s.rect(1))/s.block_width);
           s.max_block_size = s.line_width_in_blocks;
           s.characters_textures = {};
           for i = 256:-1:1
              s.characters_textures{i} = None(); 
           end
           s.text_past = {};
           s.cursor_index_0_past = {}; 
           s.cursor_index_1_past = {};
           s.action_past = {};
           s.insert_index_past = {};
           s.text = '';
           s.cursor_index_0 = 1;
           s.cursor_index_1 = 1;
           
           s.previous_cursor_index_0 = 1;
           s.previous_cursor_index_1 = 1;
           s.insert_text(text);
           
           
           s.first_text = s.text;
           s.clipboard = '';
           s.state = StatesTextBox.Active;
           
           s.button_index_cursor = 1;
           s.button_paste = 3;
           s.time_cursor_cycle_in_days = 0.8/24/60/60;
%            [~,cmdout] = system('gsettings get org.gnome.desktop.peripherals.keyboard delay'); %500
%            delay_in_ms = split(cmdout, ' ');
%            delay_in_ms = delay_in_ms{2};
%            delay_in_ms = str2double(delay_in_ms);
           delay_in_ms = 500;
           s.first_delay_keys_in_days = delay_in_ms/1000/24/60/60;
%            [~,cmdout] = system('gsettings get org.gnome.desktop.peripherals.keyboard repeat-interval'); %30
%            repeat_in_ms = split(cmdout, ' ');
%            repeat_in_ms = repeat_in_ms{2};
%            repeat_in_ms = str2double(repeat_in_ms);
           repeat_in_ms = 30;
           s.sequence_delay_keys_in_days = repeat_in_ms/1000/24/60/60; 
           
%            [~,cmdout] = system('gsettings get org.gnome.settings-daemon.peripherals.mouse double-click'); %400
%            doubleclick_in_ms = str2double(cmdout);
           doubleclick_in_ms =400;
           s.doubleclick_in_days = doubleclick_in_ms/1000/24/60/60; 
           s.doubleclick_minimum_in_days = 30/1000/24/60/60;
           s.last_click_doubleclick =None();
           
           s.cursor_drawing_time_count = now;
           s.draw_cursor=0;
           s.arrow_keys_names = {'RightArrow','LeftArrow','UpArrow','DownArrow'};
           s.arrow_keys_state = [StatesArrowKeys.Unclicked, StatesArrowKeys.Unclicked, StatesArrowKeys.Unclicked, StatesArrowKeys.Unclicked];
           s.arrow_keys_timers = {None(),None(),None(),None()};
           s.blocks_sizes = [];
           s.blocks_textures = {};
           s.redivide_texture_block(length(s.text), 1);
        end
        
        function calculate_line_sizes(s, starting_line)
            starting_line = max([starting_line-1,0]);
            line = starting_line;
            if line == 0
                last_index = 1;
            else
                last_index = s.accumulated_line_sizes(line)+1;
            end
            s.line_sizes(starting_line+1:end) = [];
            s.accumulated_line_sizes(starting_line+1:end) = [];
            
            while last_index<length(s.text)+1
                max_index_this_line = min([s.line_width_in_blocks + last_index, length(s.text)+1]);
                full_width_text_this_line = s.text(last_index:max_index_this_line-1);
                if max_index_this_line == length(s.text)+1
                    last_space = [];
                else
                    last_space = find(full_width_text_this_line == ' ', 1, 'last')+1;
                end
                first_return = find(full_width_text_this_line == 10, 1, 'first')+1;
                this_index = min([first_return, last_space, max_index_this_line-last_index+1]) + last_index-1; 

                if this_index==s.line_width_in_blocks+last_index && length(s.text)>=this_index && abs(s.text(this_index))==10
                   this_index = this_index + 1; 
                end
                s.line_sizes(line+1) = this_index - last_index ;
                s.drawing_line_sizes(line+1) = s.line_sizes(line+1) - 1*(s.text(this_index-1) == 10);
                last_index = this_index;
                s.accumulated_line_sizes(line+1) = this_index-1;
                
                line = line + 1;
            end
        end
        
        function reset(s)
            s.delete_text(1,length(s.text));
            s.insert_text(s.first_text);
        end
        
        function close_texture(s, texture)
            if ~None.isNone(texture)
                Screen('Close',texture);
            end
        end
        
        function redivide_texture_block(s,insert_length, insert_index)
            accumulated_size = 0;
            previous_acc = 0;
            if isempty(s.blocks_sizes) && insert_length>0
                s.blocks_sizes = [0];
                s.blocks_textures = {None()};
            end
            for i = 1:length(s.blocks_sizes)
                accumulated_size = accumulated_size + s.blocks_sizes(i);
                if accumulated_size>=insert_index || i == length(s.blocks_sizes)
                    s.close_texture(s.blocks_textures{i});
                    if  s.blocks_sizes(i)+insert_length > s.max_block_size
                        new_blocks = s.recursive_divide_blocks([s.blocks_sizes(i)+insert_length]);
                        delta_index = length(new_blocks)-1;
                        s.blocks_sizes = [s.blocks_sizes(1:i-1) new_blocks s.blocks_sizes(i+1:end)];
                        if length(s.blocks_textures)>=i+1
                            for k = length(s.blocks_textures):-1:i+1
                                s.blocks_textures{k+delta_index} = s.blocks_textures{k};
                            end
                        end
                        for k = 0:delta_index
                            s.blocks_textures{i+k} = Screen('MakeTexture', s.mainWindow.winMain, zeros(s.block_height+s.line_spacing, s.block_width*s.max_block_size,4), 0, 0, 1);
                            if k==0
                                delta_begin = 0;
                            else
                                delta_begin = delta_begin + s.blocks_sizes(i+k-1);
                            end
                            s.write_characters_to_texture(s.blocks_textures{i+k},s.text(previous_acc+1+delta_begin:previous_acc+delta_begin+s.blocks_sizes(i+k)));
                        end
                    elseif s.blocks_sizes(i)-(insert_index-previous_acc-1)+insert_length<=0
                        total_blocks_deleted = 1;
                        total_char_deleted = s.blocks_sizes(i)-(insert_index-previous_acc-1);

                        for k = i+1:length(s.blocks_textures)
                            if total_char_deleted+insert_length<0
                                total_char_deleted = total_char_deleted + s.blocks_sizes(k);
                                s.close_texture(s.blocks_textures{k});
                                total_blocks_deleted = total_blocks_deleted + 1;
                            else
                                break;
                            end
                        end
                        
                        if total_blocks_deleted>1 
                            if total_char_deleted~=-insert_length
                                s.blocks_sizes(i+total_blocks_deleted-1) = (total_char_deleted+insert_length);
                                s.blocks_textures{i+total_blocks_deleted-1} = Screen('MakeTexture', s.mainWindow.winMain, zeros(s.block_height+s.line_spacing, s.block_width*s.max_block_size,4), 0, 0, 1);
                                s.write_characters_to_texture(s.blocks_textures{i+total_blocks_deleted-1},s.text(insert_index:insert_index-1+s.blocks_sizes(i+total_blocks_deleted-1)));
                            else
                                s.blocks_textures(i+total_blocks_deleted-1) = [];
                                s.blocks_sizes(i+total_blocks_deleted-1) = [];
                            end
                        end
                        
                        for k = i+total_blocks_deleted-2:-1:i+1
                            s.blocks_textures(k) = [];
                            s.blocks_sizes(k) = [];
                        end
                        if insert_index-previous_acc-1>0
                            s.blocks_sizes(i) = insert_index-previous_acc-1;
                            s.blocks_textures{i} = Screen('MakeTexture', s.mainWindow.winMain, zeros(s.block_height+s.line_spacing, s.block_width*s.max_block_size,4), 0, 0, 1);
                            s.write_characters_to_texture(s.blocks_textures{i},s.text(previous_acc+1:previous_acc+s.blocks_sizes(i)));
                        else
                            s.blocks_textures(i) = [];
                            s.blocks_sizes(i) = [];
                        end
                    else
                        s.blocks_textures{i} = Screen('MakeTexture', s.mainWindow.winMain, zeros(s.block_height+s.line_spacing, s.block_width*s.max_block_size,4), 0, 0, 1);
                        s.write_characters_to_texture(s.blocks_textures{i},s.text(previous_acc+1:accumulated_size+insert_length));
                        s.blocks_sizes(i) = s.blocks_sizes(i) + insert_length;
                    end
                    break;
                end
                previous_acc = accumulated_size;
            end
        end
        
        function write_characters_to_texture(s,texture_to_draw_on,new_text)
            textures = [];
            dest_rects = [];
            for index_char = length(new_text):-1:1
                string_to_write = new_text(index_char);
                index_string_to_write = abs(string_to_write);
                if string_to_write>256
                    string_to_write = '?';
                    index_string_to_write = abs(string_to_write);
                end
                texture = s.characters_textures{index_string_to_write};
                if None.isNone(texture)
                    s.characters_textures{index_string_to_write} = Screen('MakeTexture', s.mainWindow.winMain, zeros(s.block_height+s.line_spacing, s.block_width,4), 0, 0, 1);
                    texture = s.characters_textures{index_string_to_write};
                    Screen('TextFont',texture,s.mainWindow.fontName);
                    Screen('TextSize',texture,s.mainWindow.fontSize);
                    DrawFormattedText(texture, string_to_write, 0, s.block_height, [1 1 1 1.25]);
                end
                textures(index_char) = texture;
                dest_rects(:,index_char) = [(index_char-1)*s.block_width, 0, (index_char)*s.block_width, (s.block_height+s.line_spacing)];
            end
            if ~isempty(textures)
                Screen('DrawTextures',texture_to_draw_on, textures,[],dest_rects);
            end
        end
        
        function blocks = recursive_divide_blocks(s, blocks)
            i = 1;
            while 1
                if blocks(i) > s.max_block_size
                    redivided_blocks = [floor(blocks(i)/2) ceil(blocks(i)/2)];
                    if ceil(blocks(i)/2)>s.max_block_size
                        redivided_blocks = s.recursive_divide_blocks(redivided_blocks);
                    end
                    blocks = [blocks(1:i-1) redivided_blocks blocks(i+1:end)];
                    i = i + length(redivided_blocks) - 1 ;
                end
                i = i + 1;
                if i>length(blocks)
                    break;
                end
            end
        end
        
        function set_text(s,new_text, insert_index, undo_redo)
            if ~undo_redo
                delta_text = length(new_text)-length(s.text);
                if delta_text>0
                    s.action_past{end+1} = 1;
                    s.text_past{end+1} = new_text(insert_index:insert_index+delta_text-1);
                else
                    s.action_past{end+1} = -1;
                    s.text_past{end+1} = s.text(insert_index:insert_index-delta_text-1);
                end
                s.insert_index_past{end+1} = insert_index;
                s.cursor_index_0_past{end+1} = s.cursor_index_0;
                s.cursor_index_1_past{end+1} = s.cursor_index_1;
                s.cursor_index_0_future = {};
                s.cursor_index_1_future = {};
                s.text_future = {};
                s.insert_index_future = {};
                s.action_future = {};
            end
            insert_length = length(new_text) - length(s.text);
            s.text = new_text;
            [line_change, ~] = s.convert_index_to_line_column(insert_index);
            s.calculate_line_sizes(line_change);
            s.redivide_texture_block(insert_length, insert_index);
        end
        
        function arrow_key_move(s,index)
            switch(index)
                case 1 %right
                    if s.cursor_index_0~=s.cursor_index_1
                        s.cursor_index_0 = max([s.cursor_index_0,s.cursor_index_1]);
                    else
                        s.cursor_index_0 = min([s.cursor_index_0 + 1,length(s.text)+1]);
                    end
                case 2 %left
                    if s.cursor_index_0~=s.cursor_index_1
                        s.cursor_index_0 = min([s.cursor_index_0,s.cursor_index_1]);
                    else
                       s.cursor_index_0 = max([s.cursor_index_0 - 1,1]);
                    end
                    
                case 3 %up
                    if s.cursor_index_0~=s.cursor_index_1
                        s.cursor_index_0 = min([s.cursor_index_0,s.cursor_index_1]);
                    end
                    [line, column] = s.convert_index_to_line_column(s.cursor_index_0);
                    if column>s.drawing_line_sizes(line+1)
                        line = line +1;
                        column = 0;
                    end
                    line = max([line-1,0]);
                    column = min([s.drawing_line_sizes(line+1), column]);
                    s.cursor_index_0 = s.convert_line_column_to_index(line, column);
                case 4 %down
                    if s.cursor_index_0~=s.cursor_index_1
                        s.cursor_index_0 = max([s.cursor_index_0,s.cursor_index_1]);
                    end
                    [line, column] = s.convert_index_to_line_column(s.cursor_index_0);
                    if column>s.drawing_line_sizes(line+1)
                        line = line +1;
                        column = 0;
                    end
                    [line_max, ~] = s.convert_index_to_line_column(length(s.text)+1);
                    line = min([line+1,line_max]);
                    column = min([s.drawing_line_sizes(line+1), column]);
                    s.cursor_index_0 = s.convert_line_column_to_index(line, column);
            end
            s.cursor_index_1 = s.cursor_index_0;   
            s.confirm_cursor_values;
        end
        
        function index = get_clicked_space(s,x,y)
           if x< s.rect(1)
               index_x = 0;
           elseif x > s.rect(3)
               index_x = round((s.rect(3)-s.rect(1))/s.block_width);
           else
               index_x = round((x-s.rect(1))/s.block_width);
           end
           max_y = max([length(s.line_sizes)-1,0]);
           if y< s.rect(2)
               index_y = 0;
           else
               index_y = round((y-s.rect(2)-s.block_height/2)/(s.block_height+s.line_spacing));
               if index_y>max_y
                   index_y = max_y;
               end
           end
           if ~isempty(s.line_sizes)
                index_x = min([index_x, s.line_sizes(index_y+1)]);
           else
               index_x = 0;
           end
           index = s.convert_line_column_to_index(index_y, index_x);
        end
        
        function interaction_map = interact(s, mouse, keyboard)
            xx = mouse('mouse_x');
            yy = mouse('mouse_y');
            [mouse_clicked, mouse_changed_x, mouse_changed_y] = BufferInput.get_indexed_values(mouse, s.button_index_cursor);
            cursor = '';
            if xx>s.rect(1) && xx<s.rect(3) && yy>s.rect(2)
                cursor = 152;
            end
            keyboard_buffer = keyboard('buffer');
            if ~isempty(s.drawing_line_sizes)
                if keyboard_buffer(KbName('Home'))
                    s.cursor_index_0 = min([s.cursor_index_0,s.cursor_index_1]);
                    [line, column] = s.convert_index_to_line_column(s.cursor_index_0);
                    if column>s.drawing_line_sizes(line+1)
                        line = line +1;
                    end
                    column = 0;
                    s.cursor_index_0 = s.convert_line_column_to_index(line, column);
                    s.cursor_index_1 = s.cursor_index_0;
                end
                if keyboard_buffer(KbName('End'))
                    s.cursor_index_0 = max([s.cursor_index_0,s.cursor_index_1]);
                    [line, column] = s.convert_index_to_line_column(s.cursor_index_0);
                    if column>s.drawing_line_sizes(line+1)
                        line = line +1;
                    end
                    column = s.drawing_line_sizes(line+1);
                    s.cursor_index_0 = s.convert_line_column_to_index(line, column);
                    s.cursor_index_1 = s.cursor_index_0;
                end
            
                for i = 1:length(s.arrow_keys_names)
                    if keyboard_buffer(KbName(s.arrow_keys_names{i}))
                        current_time = now;
                        switch(s.arrow_keys_state(i))
                            case StatesArrowKeys.Unclicked 
                                s.arrow_key_move(i);
                                s.arrow_keys_state(i) = StatesArrowKeys.Delay;
                                s.arrow_keys_timers{i} = current_time; 
                            case StatesArrowKeys.Delay
                                if current_time - s.arrow_keys_timers{i} > s.first_delay_keys_in_days
                                    s.arrow_key_move(i);
                                    s.arrow_keys_state(i) = StatesArrowKeys.Repeat;
                                    s.arrow_keys_timers{i} = s.arrow_keys_timers{i} + s.first_delay_keys_in_days; 
                                end
                            case StatesArrowKeys.Repeat
                                if current_time - s.arrow_keys_timers{i} > s.sequence_delay_keys_in_days
                                    s.arrow_key_move(i);
                                    s.arrow_keys_timers{i} = s.arrow_keys_timers{i} + s.sequence_delay_keys_in_days*floor((current_time - s.arrow_keys_timers{i})/s.sequence_delay_keys_in_days); 
                                end  
                        end
                    else
                       s.arrow_keys_state(i) = StatesArrowKeys.Unclicked;
                       s.arrow_keys_timers{i} = None(); 
                    end
                end
            end
            
            [mouse_paste_clicked, ~, ~] = BufferInput.get_indexed_values(mouse, s.button_paste);
            if s.state==StatesTextBox.ClickingPaste && ~mouse_paste_clicked
                s.state = StatesTextBox.Active;
            end
            if s.state==StatesTextBox.Active && mouse_paste_clicked && ~isempty(s.clipboard)
                s.new_char = s.clipboard;
                s.state = StatesTextBox.ClickingPaste;
            else
                s.new_char = keyboard('char');
                if abs(s.new_char)==17 %ctrl+q, cut
                   s.clipboard = s.get_selected_text;
                   s.erase_between_cursors;
                   s.new_char = 0; 
                end
                if abs(s.new_char)==1 %ctrl+a, redo
                    if ~isempty(s.text_future)
                        s.text_past{end+1} = s.text_future{end};
                        s.action_past{end+1} = s.action_future{end};
                        s.insert_index_past{end+1} = s.insert_index_future{end};
                        s.cursor_index_0_past{end+1} = s.cursor_index_0;
                        s.cursor_index_1_past{end+1} = s.cursor_index_1;
                        if s.action_future{end}==-1 
                            s.delete_text(s.insert_index_future{end},s.insert_index_future{end}+length(s.text_future{end})-1,1);
                        else
                            s.cursor_index_0 = s.insert_index_future{end};
                            s.cursor_index_1 = s.insert_index_future{end};
                            s.insert_text(s.text_future{end},1);
                        end
                        s.cursor_index_0 = s.cursor_index_0_future{end};
                        s.cursor_index_1 = s.cursor_index_1_future{end};
                        s.confirm_cursor_values;
                        if length(s.text_future)>1
                            s.text_future(end) = [];
                            s.cursor_index_0_future(end) = [];
                            s.cursor_index_1_future(end) = [];
                            s.action_future(end) = [];
                            s.insert_index_future(end) = [];
                        else
                            s.text_future = {};
                            s.cursor_index_0_future = {};
                            s.cursor_index_1_future = {};
                            s.action_future = {};
                            s.insert_index_future = {};
                        end
                        
                    end
                    s.new_char = 0;
                end
                if abs(s.new_char)==26 %ctrl+z, undo
                    if ~isempty(s.text_past)                   
                        s.text_future{end+1} = s.text_past{end};
                        s.action_future{end+1} = s.action_past{end};
                        s.insert_index_future{end+1} = s.insert_index_past{end};
                        s.cursor_index_0_future{end+1} = s.cursor_index_0;
                        s.cursor_index_1_future{end+1} = s.cursor_index_1;
                        if s.action_past{end}==1 
                            s.delete_text(s.insert_index_past{end},s.insert_index_past{end}+length(s.text_past{end})-1,1);
                        else
                            s.cursor_index_0 = s.insert_index_past{end};
                            s.cursor_index_1 = s.insert_index_past{end};
                            s.insert_text(s.text_past{end},1);
                        end
                        s.cursor_index_0 = s.cursor_index_0_past{end};
                        s.cursor_index_1 = s.cursor_index_1_past{end};
                        s.confirm_cursor_values;
                        if length(s.text_past)>1
                            s.text_past(end) = [];
                            s.cursor_index_0_past(end) = [];
                            s.cursor_index_1_past(end) = [];
                            s.insert_index_past(end) = [];
                            s.action_past(end) = [];
                        else
                            s.text_past = {};
                            s.cursor_index_0_past = {};
                            s.cursor_index_1_past = {};
                            s.insert_index_past = {};
                            s.action_past = {};
                        end
                    end
                    s.new_char = 0;
                end
            end
            interaction_map = containers.Map({'interacted','cursor'}, {mouse_clicked, cursor});
            if s.state==StatesTextBox.Active
                if mouse_clicked
                    current_time = now;
                    if ~None.isNone(s.last_click_doubleclick)
                        delta_click = current_time - s.last_click_doubleclick;
                        
                        if delta_click>=s.doubleclick_minimum_in_days && delta_click<=s.doubleclick_in_days
                            if s.cursor_index_0==s.get_clicked_space(mouse_changed_x,mouse_changed_y)
                                previous_cursor_index_0 = s.cursor_index_0;
                                str_before = s.text(1:previous_cursor_index_0-1);
                                s.cursor_index_0 = 0;
                                for char_index=length(str_before):-1:1
                                    if strcmp(str_before(char_index), ' ') || strcmp(str_before(char_index), '.') || strcmp(str_before(char_index), ',')
                                        s.cursor_index_0 = char_index+1;
                                        break;
                                    end
                                end
                                str_after = s.text(previous_cursor_index_0:end);
                                s.cursor_index_1 = length(s.text)+1;
                                for char_index=1:length(str_after)
                                    if strcmp(str_after(char_index), ' ') || strcmp(str_after(char_index), '.') || strcmp(str_after(char_index), ',')
                                        s.cursor_index_1 = char_index-1 + previous_cursor_index_0;
                                        break;
                                    end
                                end
                                s.state = StatesTextBox.DoubleClick;
                            end
                        end
                    end
                    if s.state~=StatesTextBox.DoubleClick
                        if s.cursor_index_0~=s.cursor_index_1
                            s.clipboard = s.get_selected_text;
                        end
                        s.cursor_index_0 = s.get_clicked_space(mouse_changed_x,mouse_changed_y);
                        s.last_click_doubleclick = current_time;
                        s.state=StatesTextBox.Clicking;
                    end
                end
            end
            if s.state==StatesTextBox.Clicking
                if ~mouse_clicked
                    s.cursor_index_1 = s.get_clicked_space(mouse_changed_x,mouse_changed_y);
                    s.state=StatesTextBox.Active;
                else
                   s.cursor_index_1 = s.get_clicked_space(xx,yy); 
                end
            end
            if s.state==StatesTextBox.DoubleClick
                if ~mouse_clicked
                    mouse_position = s.get_clicked_space(mouse_changed_x,mouse_changed_y);
                    s.state=StatesTextBox.Active;
                else
                    mouse_position = s.get_clicked_space(xx,yy); 
                end
                if mouse_position>s.cursor_index_1
                    s.cursor_index_1 = mouse_position;
                elseif mouse_position<s.cursor_index_0
                    s.cursor_index_0 = mouse_position;
                end
            end
            s.confirm_cursor_values;
        end
        
        function insert_text(s,to_insert, undo_redo)
            if ~exist('undo_redo','var')
                undo_redo = 0;
            end
            if s.cursor_index_0 == length(s.text)+1
                s.set_text([s.text to_insert], s.cursor_index_0, undo_redo);
            else
                s.set_text([s.text(1:s.cursor_index_0-1), to_insert, s.text(s.cursor_index_0:end)], s.cursor_index_0, undo_redo);
            end
            if ~undo_redo
                s.cursor_index_1 = s.cursor_index_1+length(to_insert);
                s.cursor_index_0 = s.cursor_index_0+length(to_insert);
                s.confirm_cursor_values;
            end
        end
        
        function delete_text(s,min_cursor, max_cursor_minus_one, undo_redo)
            if ~exist('undo_redo','var')
                undo_redo = 0;
            end
            s.set_text(eraseBetween(s.text, min_cursor,max_cursor_minus_one), min_cursor, undo_redo);
            if ~undo_redo
                s.cursor_index_0 = min_cursor;    
                s.cursor_index_1 = min_cursor; 
                s.confirm_cursor_values;
            end
        end
        
        function erase_between_cursors(s)
            min_cursor = min([s.cursor_index_0, s.cursor_index_1]);
            max_cursor = max([s.cursor_index_0, s.cursor_index_1]);
            s.delete_text(min_cursor,max_cursor-1); 
        end
        
        function selected_text = get_selected_text(s)
            selected_text = s.text(min([s.cursor_index_0,s.cursor_index_1]):max([s.cursor_index_0,s.cursor_index_1])-1);   
        end
        
        function confirm_cursor_values(s)
            s.cursor_index_0 = min([s.cursor_index_0,length(s.text)+1]);
            s.cursor_index_1 = min([s.cursor_index_1,length(s.text)+1]);
            s.cursor_index_0 = max([s.cursor_index_0,1]);
            s.cursor_index_1 = max([s.cursor_index_1,1]);
        end
        
        function interaction_map = update(s)
            changed = 0;
            previous_draw_cursor = s.draw_cursor;
            s.draw_cursor = 0;
            delta_cursor_time = now - s.cursor_drawing_time_count;
            if delta_cursor_time > s.time_cursor_cycle_in_days
                s.cursor_drawing_time_count = mod(delta_cursor_time,s.time_cursor_cycle_in_days)+now;
                delta_cursor_time = s.cursor_drawing_time_count - now;
            end
            if delta_cursor_time < s.time_cursor_cycle_in_days/2
                 s.draw_cursor = 1;
            end
            if s.draw_cursor~=previous_draw_cursor
                changed = 1;
            end
            if s.previous_cursor_index_1~=s.cursor_index_1 || s.previous_cursor_index_0~=s.cursor_index_0
                changed = 1;
            end
            s.previous_cursor_index_1=s.cursor_index_1;
            s.previous_cursor_index_0=s.cursor_index_0;
            if length(s.new_char)>1 || (length(s.new_char)==1 && s.new_char~=0)
                selection_made = 0;
                if s.cursor_index_0~=s.cursor_index_1
                    selection_made = 1;
                    s.erase_between_cursors;
                end
                
                changed = 1;
                if length(s.new_char)>1
                    s.insert_text(s.new_char);
                else
                    switch abs(s.new_char)
                        case 8
                            % backspace
                            if ~isempty(s.text) && ~selection_made && s.cursor_index_1>1
                                s.delete_text(s.cursor_index_1-1,s.cursor_index_1-1);
                            end
                        case 127
                            % delete
                            if ~isempty(s.text) && ~selection_made && s.cursor_index_1<length(s.text)+1
                                s.delete_text(s.cursor_index_1,s.cursor_index_1);
                            end
                        case 3
                        
                        otherwise
                            s.insert_text(s.new_char);
                    end
                end
            end
            interaction_map = containers.Map({'changed','exit'}, {changed,ChangeScreen.No});
        end
        
        function draw(s, cumulative_drawing)
            if  s.draw_cursor
                [line, column] = s.convert_index_to_line_column(s.cursor_index_1);
                if s.cursor_index_1-1>0
                    if s.text(s.cursor_index_1-1)==10
                      line = line+1;
                      column = 0;
                    end
                end
                cumulative_drawing.add_line(s.depth, [1,1,1], s.rect(1) + column*s.block_width, s.rect(2)+line*(s.block_height+s.line_spacing), s.rect(1) + column*s.block_width, s.rect(2)+(line+1)*(s.block_height+s.line_spacing));
            end
            if s.cursor_index_0~=s.cursor_index_1 
                min_cursor = min([s.cursor_index_0,s.cursor_index_1]);
                max_cursor = max([s.cursor_index_0,s.cursor_index_1]);
                [line_0, column_0] = s.convert_index_to_line_column(min_cursor);
                [line_1, column_1] = s.convert_index_to_line_column(max_cursor);
                for line = line_0:line_1
                    column_start = 0;
                    column_end = s.line_sizes(line+1);
                    if line==line_0
                        column_start = column_0;
                    end
                    if line==line_1
                       column_end = column_1; 
                    end
                   
                    cumulative_drawing.add_fill_rect(s.depth, [0.5,0.5,0.5], [s.rect(1)+column_start*s.block_width, s.rect(2)+line*(s.block_height+s.line_spacing)+1, s.rect(1)+column_end*s.block_width, s.rect(2)+(line+1)*(s.block_height+s.line_spacing)]);
                end
            end
            if ~isempty(s.text)
                [line_final, ~] = s.convert_index_to_line_column(length(s.text)+1);
                textures = [];
                source_rects = zeros(4,0);
                dest_rects = zeros(4,0);
                
                current_block = 1;
                accumulated_size = 0;
                previous_block_x_end = s.rect(1);
                already_drawn_from_blocks = zeros(length(s.blocks_sizes));
                for line = 0:line_final
                    limit_y = s.rect(1)+(s.line_sizes(line+1))*s.block_width;
                    while current_block<=length(s.blocks_sizes)
                        accumulated_size = accumulated_size + s.blocks_sizes(current_block);
                        to_break = 0;
                        width_this_drawing = s.blocks_sizes(current_block)*s.block_width - already_drawn_from_blocks(current_block);
                        
                        if previous_block_x_end + width_this_drawing >= limit_y
                            to_break = 1;
                        end
                        
                        if previous_block_x_end + width_this_drawing > limit_y
                            width_this_drawing = limit_y-previous_block_x_end;
                        end
                        
                        textures(end+1) = s.blocks_textures{current_block};
                        source_rects(:,end+1) = [already_drawn_from_blocks(current_block),0,already_drawn_from_blocks(current_block)+width_this_drawing,s.block_height+s.line_spacing];
                        already_drawn_from_blocks(current_block) = already_drawn_from_blocks(current_block) + width_this_drawing;
                        dest_rects(:,end+1) = [previous_block_x_end,s.rect(2)+line*(s.block_height+s.line_spacing),previous_block_x_end + width_this_drawing,s.rect(2)+(line+1)*(s.block_height+s.line_spacing)];
                        previous_block_x_end = previous_block_x_end + width_this_drawing;
                        if already_drawn_from_blocks(current_block)>=s.blocks_sizes(current_block)*s.block_width
                            current_block = current_block + 1;
                        end
                        if to_break
                            previous_block_x_end = s.rect(1);
                            break;
                        end
                    end
                end
                if ~isempty(textures)
                    cumulative_drawing.add_textures(s.depth,textures,source_rects,dest_rects);
                end
            end
        end
        
        function [line,column] = convert_index_to_line_column(s,index)
            index = index-1;
            if index==0
                line = 0;
                column = 0;
                return;
            end
            for i=1:length(s.accumulated_line_sizes)
                if s.accumulated_line_sizes(i)>=index
                    line = i-1;
                    if i==1
                        column = index;
                    else
                        column = index-s.accumulated_line_sizes(i-1);
                    end
                    break;
                end
            end
        end
        
        function index = convert_line_column_to_index(s,line, column)
            if line==0
                index = column+1;
            else
                index = s.accumulated_line_sizes(line)+column+1;
            end
        end
        
        function state = save_state(s)
            state = containers.Map();
            state('text') = s.text;
            state('text_future') = s.text_future;
            state('text_past') = s.text_past;
            state('insert_index_future') = s.insert_index_future;
            state('insert_index_past') = s.insert_index_past;
            state('cursor_index_0') = s.cursor_index_0;
            state('cursor_index_1') = s.cursor_index_1;
            state('cursor_index_0_past') = s.cursor_index_0_past;
            state('cursor_index_1_past') = s.cursor_index_1_past;
            state('cursor_index_0_future') = s.cursor_index_0_future;
            state('cursor_index_1_future') = s.cursor_index_1_future;
            state('action_past') = s.action_past;
            state('action_future') = s.action_future;
        end
        
        function load_state(s, state)
            insert_length = -length(s.text);
            s.text = '';
            
            [line_change, ~] = s.convert_index_to_line_column(1);
            s.calculate_line_sizes(line_change);
            s.redivide_texture_block(insert_length, 1);
            
            s.cursor_index_0 = 1;    
            s.cursor_index_1 = 1; 
            s.confirm_cursor_values;
            
            s.text = state('text');
            
            insert_length = length(s.text);
            [line_change, ~] = s.convert_index_to_line_column(1);
            s.calculate_line_sizes(line_change);
            s.redivide_texture_block(insert_length, 1);
            
            s.text_future = state('text_future');
            s.text_past = state('text_past');
            s.action_past = state('action_past');
            s.action_future = state('action_future');
            s.insert_index_future = state('insert_index_future');
            s.insert_index_past = state('insert_index_past');
            s.cursor_index_0 = state('cursor_index_0');
            s.cursor_index_1 = state('cursor_index_1');
            s.cursor_index_0_past = state('cursor_index_0_past');
            s.cursor_index_1_past = state('cursor_index_1_past');
            s.cursor_index_0_future = state('cursor_index_0_future');
            s.cursor_index_1_future = state('cursor_index_1_future');
            
            s.confirm_cursor_values; 
        end
        
        function interaction_map = before_destruction(s)
            s.mainWindow.states([num2str(s.mainWindow.screen_i), '_', s.name]) = s.save_state;
            for i = 1:length(s.characters_textures)
                s.close_texture(s.characters_textures{i});
            end
            for i = 1:length(s.blocks_textures)
                s.close_texture(s.blocks_textures{i});
            end
            resplit_string = join(strtrim(split(s.text,[";"])),"@$");
            resplit_string = join(strtrim(split(s.text,["|"])),"@$");
            resplit_string = join(strtrim(split(resplit_string{1},[newline])),"@!"); % was "@£"
            s.structured_output.add_message(class(s),'text', resplit_string{1});
            interaction_map = containers.Map({'exit'}, {ChangeScreen.No});
        end
        
    end
end