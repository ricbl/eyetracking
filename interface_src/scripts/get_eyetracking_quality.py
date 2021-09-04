from re import split

def ASC2CSV(fname):
    state_edf = 0
    screen_fixations = []
    with open(fname, 'r', encoding="utf8", errors='ignore') as ascfile:
        for current_line in ascfile:
            split_line = split('\t| ',current_line)
            split_line = [i for i in split_line if i] 
            if state_edf==0:
                if split_line[0] == 'START':
                    state_edf = 1
                    total_time_blink = 0
                    longest_blink = 0
                    time_start_capture = float(split_line[1])
            elif state_edf==1:
                if split_line[0] == 'END':
                    time_end_capture = float(split_line[1])
                    delta_time = time_end_capture-time_start_capture
                    if delta_time>0:
                        ratio_blink_total = total_time_blink/delta_time
                    else:
                        ratio_blink_total = 0
                    # best_distance_to_center = get_best_distance_to_center(screen_fixations)
                    return ratio_blink_total, longest_blink#, best_distance_to_center
                elif split_line[0] == 'EBLINK':
                    delta_time = float(split_line[3]) - float(split_line[2])
                    total_time_blink = total_time_blink + delta_time
                    longest_blink = max(longest_blink, delta_time)
                # elif split_line[0] == 'EFIX':
                #     position_x_screen = float(split_line[5])
                #     position_y_screen = float(split_line[6])
                #     time_end = float(split_line[3])
                #     screen_fixations.append([position_x_screen, position_y_screen, time_end])

def get_best_distance_to_center(screen_fixations):
    center_next = [330, 1077.5]
    best_fixation_in_margin = None
    time_last_fixation = screen_fixations[-1][-1]
    for fixation in screen_fixations:
        px,py, timestamp = fixation
        if px<660 and time_last_fixation-timestamp<3000:
            current_distance_to_center = distance([px,py],center_next)
            if (best_fixation_in_margin is None or current_distance_to_center<best_distance_to_center):
                best_fixation_in_margin = [px,py]
                best_distance_to_center = current_distance_to_center
    if best_fixation_in_margin is not None:
        return distance([center_next[0],best_fixation_in_margin[1]],center_next)
    else: 
        return -1

def distance(p1, p2):
    return ((p2[0]-p1[0])**2+(p2[1]-p1[1])**2)**0.5

def main():
    import argparse
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--file_name', type=str, nargs='?',
                        help='name of the edf file, without the .EDF extension.')
    args = parser.parse_args()
    # ratio_blink_total, longest_blink, best_distance_to_center = ASC2CSV(args.file_name[:-4] + '.asc')
    ratio_blink_total, longest_blink = ASC2CSV(args.file_name[:-4] + '.asc')
    with open(args.file_name + '_warning.txt', "w") as text_file:
        text_file.write(str(ratio_blink_total)+'\n')
        text_file.write(str(longest_blink)+'\n')
        
        # text_file.write(str(best_distance_to_center))

if __name__ == "__main__":
    main()