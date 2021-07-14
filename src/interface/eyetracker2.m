classdef eyetracker2 < handle
   properties
      edfFile; 
      structured_output;
      runDir;
      el;
      count_screen;
      trial;
      mainWindow;
      part_1_edffile;
      part_2_edffile;
      gonne_to_part_2;
   end
   methods
       function s = eyetracker2(el, runDir, structured_output, main_window)
           s.mainWindow = main_window;
           s.runDir = runDir;
           s.el = el;
           s.structured_output = structured_output;
           s.count_screen = 0;
           s.gonne_to_part_2 = 0;
%            s.edfFile = strcat(runDir, "/et.EDF");
           %s.edfFile = strcat("et", num2str(s.structured_output.current_trial), '.EDF');
           experiment_folder = strsplit(s.runDir,filesep);
           experiment_folder = experiment_folder{end};
           experiment_folder = experiment_folder(end-3:end);
           s.edfFile = strcat("inpupil.EDF");
           edffilename = char(s.edfFile);
           
            [~, vs] = Eyelink('GettrackerVersion');
            fprintf('Running experiment on a ''%s'' tracker.\n', vs);

            % open file to record data to
            i = Eyelink('Openfile', edffilename);
            
            if i ~= 0
                Eyelink( 'Shutdown');
                return;
            end

            Eyelink('command', 'add_file_preamble_text ''Recorded by EyelinkToolbox demo-experiment''');
            [width, height] = Screen('WindowSize', main_window.screenNumber);

            % STEP 7
            % SET UP TRACKER CONFIGURATION
            % Setting the proper recording resolution, proper calibration type,
            % as well as the data file content;
            Eyelink('command','screen_pixel_coords = %ld %ld %ld %ld', 0, 0, width-1, height-1);
            Eyelink('message', 'DISPLAY_COORDS %ld %ld %ld %ld', 0, 0, width-1, height-1);
            % set calibration type.
            Eyelink('command', 'calibration_type = HV13');
            % set parser (conservative saccade thresholds) hier kriegt DOS info zu
           
            % filter for online abfrage, gaze contingent
            Eyelink('command', 'saccade_velocity_threshold = 35');
            Eyelink('command', 'saccade_acceleration_threshold = 9500');
            % set EDF file contents
            Eyelink('command', 'file_event_filter = LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON');
            Eyelink('command', 'file_sample_data  = LEFT,RIGHT,GAZE,HREF,AREA,GAZERES,STATUS');
            % set link data (used for gaze cursor)
            Eyelink('command', 'link_event_filter = LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON');
            Eyelink('command', 'link_sample_data  = LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS');
            % allow to use the big button on the eyelink gamepad to accept the
            % calibration/drift correction target
            Eyelink('command', 'button_function 5 "accept_target_fixation"');
            Eyelink('command', 'sample_rate = %d', 1000);
            % make sure we re still connected.
            if Eyelink('IsConnected')~=1
                return;
            end

            % STEP 6
            % Calibrate the eye tracker
            % setup the proper calibration foreground and background colors

            Screen('HideCursorHelper', main_window.winMain);
            s.recalibrate;

            eye_used = Eyelink('EyeAvailable'); % get eye that s tracked
            %0= left
            %1 = right
            if eye_used == el.BINOCULAR % if both eyes are tracked
                eye_used = el.LEFT_EYE; % use left eye
            end
       end
       
       function recalibrate(s)
            EyelinkDoTrackerSetup(s.el);
       end
       
       function start_recording(s,messenger)
           s.count_screen = s.count_screen + 1;
            Eyelink('StartRecording');
            s.structured_output.add_message(messenger,'start_eye_recording');
            s.structured_output.add_message(messenger,'edf_file', s.edfFile);
             s.structured_output.add_message(messenger,'edf_trial', s.count_screen);
            s.structured_output.add_message(messenger,'eye_id', Eyelink('EyeAvailable'));
       end
        
       function end_recording(s,messenger)
           s.structured_output.add_message(messenger,'end_eye_recording');
            Eyelink('StopRecording');
            if s.count_screen==1 & s.trial>0 & ~s.gonne_to_part_2
                s.part_1_edffile = ['/home/eye/Documents/projects/eyetracking/src/interface/' s.runDir '/' s.edfFile];
                s.save_edf;
                s.start_new_et_file('pt2')
                s.part_2_edffile = ['/home/eye/Documents/projects/eyetracking/src/interface/' s.runDir '/' s.edfFile];
                s.gonne_to_part_2 = 1;
            end
       end
       
       function set_eyetracker_trial(s,trial)
           s.trial = trial;
           s.start_new_et_file('')
       end    
       
       function start_new_et_file(s, prefix)
           trial = s.trial;
           s.edfFile = strcat('et',num2str(trial),prefix, '.EDF');
            edffilename = char(s.edfFile);
            %close the eye tracker.
            i = Eyelink('Openfile', edffilename);
            s.count_screen = 0;
            s.gonne_to_part_2 = 0;
            if i ~= 0
                Eyelink( 'Shutdown');
                return;
            end
            
            Eyelink('Message', 'TRIALID %d', trial);
            Eyelink('Message', 'PREFIXID %s', prefix);
            % This supplies the title at the bottom of the eyetracker display
            Eyelink('command', 'record_status_message "TRIAL %d', trial);

            Eyelink('Command', 'set_idle_mode');
            % clear tracker display and draw box at center
            Eyelink('command', 'clear_screen %d', 0');
            
            % STEP 7.3
            % start recording eye position
            Eyelink('Command', 'set_idle_mode');
            ShowCursor();
            WaitSecs(0.05);
       end
       
       function save_edf(s)
           edfFile = s.edfFile;
            Eyelink('Command', 'set_idle_mode');
            Eyelink('CloseFile');
            
            try
                fprintf('Receiving data file ''%s''\n', edfFile );
                status = Eyelink('ReceiveFile');
            catch
                fprintf('Problem receiving data file ''%s''\n', edfFile);
            end
            copyfile(edfFile, s.runDir);
       end
       
       function add_message(s,message)
          message = char(strrep(message, '%',''));
          if length(message)>199
              message = message(1:199);
          end
          Eyelink('Message', message);
       end
   end
end