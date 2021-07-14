classdef StructuredOutput  < handle
    properties
        the_table;
        current_trial;
        et;
        empty;
        local;
        current_screen;
    end
    methods
        function s = StructuredOutput(local)
            s.local = local;
            s.the_table = table({'StructuredOutput'},[datenum(datetime('now'))],...
                  {'Start'},{'None'}, [0], [0], {class('None')},...
                  'VariableNames',{'messenger', 'timestamp', 'title', 'value', 'trial', 'screen', 'type'});
            s.current_trial = 0;
            s.current_screen = 0;
        end
        
        function add_et(s,et)
            s.et = et;
        end 
       
        function add_message(s, messenger, title, value)
            struct_message.messenger = messenger;
            struct_message.title = title;
            if ~exist('value','var') || None.isNone(value)
                value = 'None';
            end
            struct_message.value = value;
            struct_message.trial = s.current_trial;
            struct_message.screen = s.current_screen;
            struct_message.timestamp = datenum(datetime('now'));
            struct_message.type = class(value);
            s.the_table = [s.the_table;struct2table(struct_message, 'AsArray',true)];
            
            %maximum of 199 characters per eyetracker message. Breaking it
            value_string = num2str(value);
            
            header_alone = sprintf('SOM953 %s;$%s;$%s;$;$%d;$%d;$%s', messenger,sprintf('%.15f', struct_message.timestamp), title, s.current_trial, s.current_screen, class(value));
            n_characters_header = length(header_alone);
            n_characters_value = length(value_string);
            available_characters_value = (194-n_characters_header);
            if available_characters_value>0
                if n_characters_header>0
                    current_value_index = 1;
%                     for i = 1:ceil(n_characters_value/available_characters_value)
%                         s.et.add_message( sprintf('SOM953 %s;$%s;$%s;$%s;$%d;$%d;$%s', messenger,sprintf('%.15f', struct_message.timestamp), title, value_string(current_value_index:min([current_value_index+available_characters_value,n_characters_value])), s.current_trial, s.current_screen, class(value)));
%                         current_value_index = current_value_index+available_characters_value + 1;
%                     end
                    total_lines = ceil(n_characters_value/available_characters_value);
                    for i = 1:total_lines
                        if total_lines>1
                            if i==total_lines
                                message_code = 'SOM955';
                            else
                                message_code = 'SOM954';
                            end
                        else
                            message_code = 'SOM953';
                        end
                        s.et.add_message( sprintf('%s %s;$%s;$%s;$%s;$%d;$%d;$%s',message_code, messenger,sprintf('%.15f', struct_message.timestamp), title, value_string(current_value_index:min([current_value_index+available_characters_value,n_characters_value])), s.current_trial, s.current_screen, class(value)));
                        current_value_index = current_value_index+available_characters_value + 1;
                    end
                else
                    s.et.add_message(header_alone);
                end
            end
        end
        
        function delete(s)
           s.save; 
        end
        
        function save(s)
            writetable(s.the_table, strcat(s.local, '/structured_output.csv'));
        end
    end

end