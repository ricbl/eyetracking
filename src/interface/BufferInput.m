classdef BufferInput < handle
   properties
       mouse_change_x;
       mouse_change_y;
       buffer;
       buffer_previous_get;
       buffer_previous_update;
       size_of_buffer;
   end
   methods
       function s = BufferInput(size_of_buffer)
           s.size_of_buffer = size_of_buffer;
           [s.mouse_change_x{1:size_of_buffer}] = deal(None());
           [s.mouse_change_y{1:size_of_buffer}] = deal(None());
           s.buffer = zeros(1, size_of_buffer);
           s.buffer_previous_get = s.buffer;
           s.buffer_previous_update = s.buffer;
       end
       
       function update_mouse(s, input_vector, coordinates_at_change)
           [mouse_x, mouse_y, ~] = GetMouse();
           indices_different = xor(s.buffer_previous_get, input_vector);
           s.buffer = (input_vector & indices_different)|(~indices_different & s.buffer);
           indices_changed = xor(s.buffer,s.buffer_previous_update);
           if sum(indices_changed)>0
               s.mouse_change_x(logical(indices_changed)) = mat2cell(coordinates_at_change(logical(indices_changed),1),1);
               s.mouse_change_y(logical(indices_changed)) = mat2cell(coordinates_at_change(logical(indices_changed),2),1);
           end
           s.buffer_previous_update = s.buffer;
       end
       
      function update(s, input_vector)
           [mouse_x, mouse_y, ~] = GetMouse();
           indices_different = xor(s.buffer_previous_get, input_vector);
           s.buffer = (input_vector & indices_different)|(~indices_different & s.buffer);
           indices_changed = xor(s.buffer,s.buffer_previous_update);
           s.mouse_change_x(logical(indices_changed)) = {mouse_x};
           s.mouse_change_y(logical(indices_changed)) = {mouse_y};
           s.buffer_previous_update = s.buffer;
       end
       
       function  to_return = get(s)
           to_return = containers.Map({'buffer', 'mouse_change_x', 'mouse_change_y'},{s.buffer, s.mouse_change_x, s.mouse_change_y});
           s.buffer_previous_get = s.buffer;
           s.buffer_previous_update = s.buffer;
           [s.mouse_change_x{1:s.size_of_buffer}] = deal(None());
           [s.mouse_change_y{1:s.size_of_buffer}] = deal(None());
       end
   end
   
   methods(Static)
       function [button_clicked, mouse_changed_x, mouse_changed_y] = get_indexed_values(inputs, index)
            mouse_changed_x = inputs('mouse_change_x');
            mouse_changed_x = mouse_changed_x{index};
            mouse_changed_y = inputs('mouse_change_y');
            mouse_changed_y = mouse_changed_y{index};
            button_clicked = inputs('buffer');
            button_clicked = button_clicked(index);
       end
   end
end