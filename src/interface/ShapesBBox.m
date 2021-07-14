classdef ShapesBBox
   enumeration
      Ellipse, Rectangle
   end
   methods
       function frame_string = get_frame_string(s)
           switch(s)
               case ShapesBBox.Rectangle
                   frame_string = 'FrameRect';
               case ShapesBBox.Ellipse
                   frame_string = 'FrameOval';
           end
       end
       
       function thickness = get_thickness(s)
           switch(s)
               case ShapesBBox.Rectangle
                   thickness = 2;
               case ShapesBBox.Ellipse
                   thickness = 2;
           end
       end
   end
   
end