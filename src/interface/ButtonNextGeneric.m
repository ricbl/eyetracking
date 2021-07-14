classdef ButtonNextGeneric < MyButton
    methods
        function s = ButtonNextGeneric(varargin)
            s@MyButton(varargin{:});
            s.attach_function_clicked(@(a)set_to_move_next(a));
        end
        

    end
end

function set_to_move_next(s)
    s.exit_return = ChangeScreen.NextScreen;
end
