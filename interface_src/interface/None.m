classdef None
    methods
        function s = None()
        end
    end
    methods(Static)
        function is_none = isNone(x)
            is_none = isa(x, 'None');
        end
        
        function update()
        end
    end
end