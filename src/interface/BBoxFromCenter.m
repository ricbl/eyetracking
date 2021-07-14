classdef BBoxFromCenter < BBox
    properties
        sqrt2correction;
    end
    methods
        function s = BBoxFromCenter(varargin)
            s@BBox(varargin{:});
            s.sqrt2correction = 0;
            s.bbox_from_center = 1;
        end
        
        function return_value = is_over_(s,i,x,y)
            return_value = false; 
            if i>4
                return;
            end
            if ~None.isNone(s.rect)
                x_center = s.rect(1);
                y_center = s.rect(2);
                [x_radius,y_radius] = s.get_radius(s.rect);
                if s.shape_box == ShapesBBox.Ellipse && s.sqrt2correction
                    if s.get_ellipse_position_relative_to_point(s,x,y,x_center,y_center,x_radius/2,y_radius/2) >=1
                        if i<=2
                            return;
                        end
                    else
                        if i>2
                            return;
                        end
                    end
                else
                    if s.hit(abs(x-x_center),abs(y-y_center),0,0, x_radius/2, y_radius/2)
                        if i>2
                            return;
                        end
                    else
                        if i<=2
                            return;
                        end
                    end
                end
                if i>2
                    if s.shape_box == ShapesBBox.Ellipse && s.sqrt2correction
                        return_value = (s.get_ellipse_position_relative_to_point(s,x,y,x_center,y_center,x_radius-s.margin,y_radius-s.margin) >=1) && ...
                            (s.get_ellipse_position_relative_to_point(s,x,y,x_center,y_center,x_radius+s.margin,y_radius+s.margin)<=1);
                    elseif s.shape_box == ShapesBBox.Ellipse
                        if i==3
                            return_value = s.hit(abs(x-x_center),abs(y-y_center),x_radius-s.margin,0, x_radius+s.margin, y_radius+s.margin);
                        elseif i==4
                            return_value = s.hit(abs(x-x_center),abs(y-y_center),0,y_radius-s.margin, x_radius+s.margin, y_radius+s.margin);
                        end
                    elseif s.shape_box == ShapesBBox.Rectangle
                        correct_rect = s.rect;
                        s.rect = s.convert_coordinates_to_corner(s.rect);
                        return_value = is_over_@BBox(s,i,x,y) || is_over_@BBox(s,i-2,x,y);
                        s.rect = correct_rect;
                    end
                else
                    return_value = s.hit(x,y,x_center-s.margin,y_center-s.margin, x_center+s.margin, y_center+s.margin);
                end
            end
        end 
        
        function to_return = get_delta_margin(s,coord,i)
            if i<=2
                to_return = get_delta_margin@BBox(s,coord,i);
            else
                opt_1 = get_delta_margin@BBox(s,coord,i);
                opt_2 = get_delta_margin@BBox(s,coord+2*(s.rect(i-2)-coord),i);
                if abs(opt_1)>abs(opt_2)
                    to_return = opt_2;
                else
                    to_return = opt_1;
                end
            end
                
        end
        
        function interaction_map = interact(s, mouse, keyboard)
            new_rectangle = 1;
            if length(s.rect)==4 && s.state == StatesBBox.Editing
                previous_rect_1 = s.rect(1);
                previous_rect_2 = s.rect(2);
                new_rectangle = 0;
            end
            interaction_map = interact@BBox(s, mouse, keyboard);
            if interaction_map('interacted')
                if length(s.rect)==4 && ~new_rectangle
                    s.rect(3) = s.rect(3) + (s.rect(1)-previous_rect_1);
                    s.rect(4) = s.rect(4) + (s.rect(2)-previous_rect_2);
                end
            end
        end
        
        function [x_radius,y_radius] = get_radius(s,rect)
            x_radius = abs(rect(3) - rect(1));
            y_radius = abs(rect(4) - rect(2));
            if s.shape_box == ShapesBBox.Ellipse && s.sqrt2correction
                x_radius =sqrt(2)*x_radius;
                y_radius =sqrt(2)*y_radius;
            end
        end
        
        function return_rect = convert_coordinates_to_corner(s, rect)
            x_center = rect(1);
            y_center = rect(2);
            [x_radius,y_radius] = s.get_radius(rect);
            return_rect = [x_center-x_radius y_center-y_radius ...
                        x_center+x_radius y_center+y_radius];
        end
        
        function [x,y] = get_label_coordinates(s,rect, shape)
            rect2 = s.convert_coordinates_to_corner(rect);
            [x,y] = get_label_coordinates@BBox(s,rect2, shape);
        end
        
        function draw_rect(s, color, rect, shape, draw_crosses, is_saved_rect, cumulative_drawing)
            rect_old_coordinates = s.convert_coordinates_to_corner(rect);
            draw_rect@BBox(s,color,rect_old_coordinates, shape, ~s.sqrt2correction && draw_crosses, is_saved_rect, cumulative_drawing);
            rect_ = s.convert_saved_rect_to_screen(rect);
        end
        
    end
end