function test_keyboard_keycodes
    time_start = GetSecs;
    [~, ~, keyboard, ~] = KbCheck();
    previous_indices = find(keyboard);
    while GetSecs - time_start < 10
        [~, ~, keyboard, ~] = KbCheck();
        indices = find(keyboard);
        if ~isequal(indices,previous_indices)
            for i = 1:length(indices)
                KbName(indices(i))
                indices(i)
            end
            previous_indices = indices;
        end
    end
end            
