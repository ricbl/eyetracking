# Example of the kind of filtering that might be applied to the fixations, to remove fixations that were not on the chest x-ray
# the defined rules are arbitrary, and the optimal filtration may depend on application, so use this code as just an example

import pandas as pd
import numpy as np
from dataset_locations import reflacx_dataset_location

def filter_fixations(id):
    fixations_df = pd.read_csv(f'{reflacx_dataset_location}/main_data/{id}/fixations.csv')
    print(len(fixations_df))
    filtered_fixations = []
    for index, row in fixations_df.iterrows():
        
        shown_rects_image_space = [round(row['xmin_shown_from_image']) ,round(row['ymin_shown_from_image']),round(row['xmax_shown_from_image']),round(row['ymax_shown_from_image'])]
        shown_rects_screen_space = [round(row['xmin_in_screen_coordinates']) ,round(row['ymin_in_screen_coordinates']),round(row['xmax_in_screen_coordinates']),round(row['ymax_in_screen_coordinates'])]
        
        #Location of the group of button, to go to next screen and to reset the image state
        buttons_rectangle = np.array([10,933,650, 1122])

        image_pixels_per_screen_pixel_x = (shown_rects_image_space[2]-shown_rects_image_space[0])/(shown_rects_screen_space[2]-shown_rects_screen_space[0])
        image_pixels_per_screen_pixel_y = (shown_rects_image_space[3]-shown_rects_image_space[1])/(shown_rects_screen_space[3]-shown_rects_screen_space[1])
        
        x_screen, y_screen = convert_image_to_screen_coordinates(row['x_position'], row['y_position'], shown_rects_screen_space, shown_rects_image_space)
        
        #distance between fixation location and the part of the screen showing the image, in screen pixels
        distance_to_image = distance_point_rectangle([x_screen, y_screen],shown_rects_screen_space)
        
        #distance to button region, in pixels
        distance_to_buttons = distance_point_rectangle([x_screen, y_screen],buttons_rectangle)
        
        #distance between fixation location and the part of the screen showing the image, in degrees
        distance_to_image_angle = distance_point_rectangle([x_screen, y_screen],shown_rects_screen_space, image_pixels_per_screen_pixel_x/row['angular_resolution_x_pixels_per_degree'], image_pixels_per_screen_pixel_y/row['angular_resolution_y_pixels_per_degree'])
        
        # keep fixations that have a position inside the image or ( that are at least 50 pixels away from buttons and at most 0.5 degrees from the image) 
        if distance_to_image==0 or (distance_to_buttons>50 and distance_to_image_angle<0.5):
            filtered_fixations.append(row)
    print(len(filtered_fixations))
    return pd.DataFrame(filtered_fixations)

def convert_screen_to_image_coordinates(x, y, dest_rect, source_rect):
    return interpolate_2d(dest_rect, source_rect, x,y);

def convert_image_to_screen_coordinates(x, y, dest_rect, source_rect):
    return interpolate_2d(source_rect,dest_rect,x,y);

def interpolate_2d(source_rect, dest_rect, x,y):
    x_scale = (dest_rect[2]-dest_rect[0])/(source_rect[2]-source_rect[0]);
    y_scale = (dest_rect[3]-dest_rect[1])/(source_rect[3]-source_rect[1]);
    return_x = x_scale*(x-source_rect[0])+dest_rect[0];
    return_y = y_scale*(y-source_rect[1])+dest_rect[1];
    return return_x,return_y

def check_inside_rect(p, rect):
    return p[0]>=rect[0] and p[0]<=rect[2] and p[1]>=rect[1] and p[1]<=rect[3]

def distance_point_rectangle(p, rect,multiplier_x = 1, multiplier_y = 1):
    if check_inside_rect(p, rect):
        return 0
    return  nearest_distance(rect, p,multiplier_x, multiplier_y)

def nearest_distance(rectangle, point,multiplier_x = 1, multiplier_y = 1):
    if point[0]>=rectangle[0] and point[0]<=rectangle[2]:
        d_top = abs(rectangle[1] - point[1])*multiplier_y
        d_bottom = abs(rectangle[3] - point[1])*multiplier_y
    else:
        d_top =float('inf')
        d_bottom=float('inf')
    corner_y = rectangle[1] if d_top < d_bottom else rectangle[3]
    if point[1]>=rectangle[1] and point[1]<=rectangle[3]:
        d_left = abs(rectangle[0] - point[0])*multiplier_x
        d_right = abs(rectangle[2] - point[0])*multiplier_x
    else:
        d_left = float('inf')
        d_right = float('inf')
    corner_x = rectangle[0] if d_left < d_right else rectangle[2]
    d_cx = corner_x - point[0]
    d_cy = corner_y - point[1]
    d_corner = ((d_cx*multiplier_x)**2 + (d_cy*multiplier_x)**2)**0.5
    return min(d_top, d_bottom, d_left, d_right, d_corner)

if __name__ == '__main__':    
    filter_fixations('P300R169761')