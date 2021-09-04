classdef SkipBoxScreen < handle
    properties
        list_disease_forbidden_box_if_not_selected;
        list_disease_required_box_if_selected;
    end
    methods
        
        function s = SkipBoxScreen(list_disease_forbidden_box_if_not_selected,list_disease_required_box_if_selected)
            s.list_disease_forbidden_box_if_not_selected = list_disease_forbidden_box_if_not_selected;
            s.list_disease_required_box_if_selected = list_disease_required_box_if_selected;
        end
        
        function to_return = get_skip_box_screen(s, chosen, single_choice_list)   
            to_return = 0;
            if all(s.list_disease_forbidden_box_if_not_selected(logical(~chosen(logical(~single_choice_list)))))
                to_return = 1;
            end

            if sum(s.list_disease_required_box_if_selected(logical(chosen(logical(~single_choice_list)))))==0
                to_return  =1;
            end
        end
    end
end