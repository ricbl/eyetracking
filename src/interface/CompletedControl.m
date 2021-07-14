classdef CompletedControl < handle
    properties
        total_cases_completed;
        total_cases;
        total_cases_completed_this_session;
    end
    methods
        function s = CompletedControl(total_cases_completed, total_cases)
            s.total_cases_completed = total_cases_completed;
            s.total_cases_completed_this_session = 0;
            s.total_cases = total_cases;
        end
        
        function case_not_completed(s)
%             s.total_cases_completed = s.total_cases_completed - 1;
%             s.total_cases_completed_this_session = s.total_cases_completed_this_session - 1;
        end
        
        function case_completed(s)
            s.total_cases_completed = s.total_cases_completed + 1;
            s.total_cases_completed_this_session = s.total_cases_completed_this_session + 1;
        end
        
        function to_return = get_string_cases_complete(s)
            to_return = ['You collected data for ',num2str(s.total_cases_completed),' cases.'];
        end
        
        function to_return = all_completed(s)
            to_return = s.total_cases_completed >= s.total_cases;
        end
    end
end