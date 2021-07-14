classdef InteractiveScreen < InteractiveCollectionSameDepth
    properties
        depth_layers;
        cumulative_drawing;
        moviePtr;
        current_secs_for_video;
        previous_secs_for_video;
        video_framerate;
    end
    methods
        function write_video_frame(s)
            if s.mainWindow.record_video==1
                s.current_secs_for_video = GetSecs;
                rounded_added_frame = round((s.current_secs_for_video-s.previous_secs_for_video)*s.video_framerate);
                residual = ((s.current_secs_for_video-s.previous_secs_for_video)*s.video_framerate-rounded_added_frame)/s.video_framerate;
                if rounded_added_frame>0
                    Screen('AddFrameToMovie', s.mainWindow.winMain,  [], 'backBuffer', s.moviePtr, rounded_added_frame);
                end
                s.previous_secs_for_video = s.current_secs_for_video - residual;
                
            end
        end
        
        function s = InteractiveScreen(mainWindow, elements)
            depth_layers = containers.Map('KeyType','int32', 'ValueType','any');
            for ii = 1:length(elements)
                elements_list = elements{ii}.get_drawable_elements_list;
                for jj = 1:length(elements_list)
                    element = elements_list{jj};
                    if ~isKey(depth_layers, element.depth)
                        depth_layers(element.depth) = {};
                    end
                    depth_layers(element.depth) = [depth_layers(element.depth), {element}];
                end
            end
            ordered_elements = {};
            for k=keys(depth_layers)
               for element = depth_layers(k{1})
                   ordered_elements(end+1) = element;
               end
            end
            s@InteractiveCollectionSameDepth(0, 'InteractiveScreen',mainWindow, ordered_elements, 1);
            s.depth_layers = depth_layers;
            
            s.parent = mainWindow;
            s.mainWindow = mainWindow;
            s.structured_output = s.parent.structured_output;
        end
        
        function interaction = main_loop(s)
            Screen('FillRect', s.mainWindow.winMain, [0 0 0], []);
            for ii = length(s.elements):-1:1
               s.elements{ii}.on_instantiation(s);
            end
            exit = ChangeScreen.No;
            WaitSecs(0.25);
            changed = 1;
            count_draws=0;
            ShowCursor('CrossHair');
            FlushEvents('keyDown');
            mouse = MouseInput;
            keyboard = KeyboardInput;
            
            if s.mainWindow.record_video>0
                for ntimes_screen = 1:999
                    filename_video = [s.structured_output.local '/recorded_screen_' num2str(s.structured_output.current_screen) '_trial_' num2str(s.structured_output.current_trial) '_' sprintf('%04d',ntimes_screen)];
                    if isfile(filename_video)
                        continue;
                    else
                        break;
                    end
                end
            end
            
            if s.mainWindow.record_video==1
                s.video_framerate = 30;
                s.moviePtr = Screen('CreateMovie', s.mainWindow.winMain, [filename_video '.mov'],[],[], s.video_framerate, ':CodecSettings=Videoquality=0.9 Profile=0',3,8);
                s.structured_output.add_message('MainWindow', 'start_video_recording');
                s.previous_secs_for_video = GetSecs;
            end
            if s.mainWindow.record_video==2
                [~,~] = system(['../../run_recording_screen.sh --fps 30 -o ' filename_video '.ogv --overwrite --no-sound > ' filename_video '.txt']);
                s.structured_output.add_message('MainWindow', 'start_video_recording');
            end
            previous_get_secs = GetSecs;
            s.cumulative_drawing = CumulativeDrawing(s.mainWindow);
            iterations_run = 0;
            while exit==ChangeScreen.No
                
                
                if s.middle_screen_changed_last_update || s.cumulative_drawing.frame_to_draw_all
                    Screen('FillRect', s.mainWindow.winMain, [0 0 0], [s.mainWindow.margin 0 s.mainWindow.screenRect(3)-s.mainWindow.screenRect(1)-s.mainWindow.margin s.mainWindow.screenRect(4)-s.mainWindow.screenRect(2)]); 
                end
                if changed || s.cumulative_drawing.frame_to_draw_all
%                     Screen('FillRect', s.mainWindow.winMain, [0 0 0], []);
                    s.draw(mouse,keyboard,s.cumulative_drawing);
                    count_draws = count_draws + 1;
                    current_get_secs = GetSecs;
                    %DrawFormattedText(s.mainWindow.winMain, num2str(count_draws), 'center', 'center', [1 1 1], 50);
                    %DrawFormattedText(s.mainWindow.winMain, num2str(1/(current_get_secs-previous_get_secs)), 'center', 'center', [0.5 0.5 0.5], 50);
                    Screen('Flip', s.parent.winMain, 0, 1);
                    s.write_video_frame;
                end
                s.cumulative_drawing.reset();
                previous_get_secs = current_get_secs;
                mouse.update();
                keyboard.update();
                mouse_inputs = mouse.get();
                keyboard_inputs = keyboard.get();
                interaction = s.interact(mouse_inputs, keyboard_inputs, mouse, keyboard);
                if ~strcmp(interaction('cursor'),'')
                   ShowCursor(interaction('cursor'));
                else
                   ShowCursor('CrossHair');
                end
                interaction = s.update(mouse, keyboard);
                changed = interaction('changed');
                exit = interaction('exit');
                iterations_run = iterations_run +1;
%                 if iterations_run>5
%                    exit = ChangeScreen.NextScreen;
%                    interaction('exit') = exit;
%                 end
                
            end
            if s.mainWindow.record_video==1
                s.write_video_frame;
                s.structured_output.add_message('MainWindow', 'end_video_recording');
                Screen('FinalizeMovie', s.moviePtr);
            end
            if s.mainWindow.record_video==2
                s.structured_output.add_message('MainWindow', 'end_video_recording');
                recording_pid = splitlines(fileread([filename_video '.txt']));
                system(['kill -15 ' num2str(recording_pid{1})]);
            end
            
            for ii = length(s.elements):-1:1
               interaction_end = s.elements{ii}.before_destruction();
               if interaction_end('exit')~=ChangeScreen.No
                   interaction = interaction_end;
               end
            end
        end
    end
end