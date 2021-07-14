classdef InteractiveDictation < InteractiveTemplate
    properties
        recObj;
        runDir;
        recording;
        device_name;
        use_psych;
        pahandle;
    end
    methods

        function s = InteractiveDictation(mainWindow)
            s@InteractiveTemplate(Depths.recording_depth, 'InteractiveDictation', mainWindow, 0);
            s.runDir = s.structured_output.local;
            s.device_name = 'PowerMicII-NS: USB Audio (hw:1,0) (ALSA)';   
            s.use_psych = 1;
            s.structured_output.add_message(class(s),'use_psych', s.use_psych);
        end
        
        function on_instantiation(s, parent)
            on_instantiation@InteractiveTemplate(s,parent);
            if ~s.use_psych
                %recording with matlab seems to miss around 1% of audio,
                %better to use psychtoolbox
                audio_devices = audiodevinfo;
                for ii = 1:length(audio_devices.input)
                    device = audio_devices.input(ii);
                    if strcmp(device.Name, s.device_name)
                        device_id = device.ID;
                        break;
                    end
                end
                s.recObj = audiorecorder(48000,16,1,device_id);
                record(s.recObj);
            else
                audio_devices = PsychPortAudio('GetDevices');
                for ii = 1:length(audio_devices)
                    device = audio_devices(ii);
                    if strcmp(device.DeviceName, s.device_name(1:end-7))
                        device_id = device.DeviceIndex;
                        break;
                    end
                end
                InitializePsychSound(1);
                % Open audio device 'device', with mode 2 (== Only audio capture),
                % and a required latencyclass of 1 == low-latency mode, with the preferred
                % default sampling frequency of the audio device, and 2 sound channels
                % for stereo capture. This returns a handle to the audio device:
                
                s.pahandle = PsychPortAudio('Open', device_id, 2, 3, 48000, 1);

                % Preallocate an internal audio recording  buffer with a capacity of 10 seconds:
                PsychPortAudio('GetAudioData', s.pahandle, 4*60);

                % Start audio capture immediately and wait for the capture to start.
                % We set the number of 'repetitions' to zero,
                % i.e. record until recording is manually stopped.
                PsychPortAudio('Start', s.pahandle, 0, 0, 1);

            end
            s.structured_output.add_message(class(s),'start_audio_recording');
            s.recording = true;
        end  
        
        function interaction_map = before_destruction(s)
            s.structured_output.add_message(class(s),'end_audio_recording');
            
            if ~s.use_psych
                stop(s.recObj);
                y = getaudiodata(s.recObj);
            else
                % Stop capture:
                PsychPortAudio('Stop', s.pahandle);

                % Perform a last fetch operation to get all remaining data from the capture engine:
                y = PsychPortAudio('GetAudioData', s.pahandle);

                % Close the audio device:
                PsychPortAudio('Close', s.pahandle);
            end


            filename = char(strcat(s.runDir, "/", int2str(s.structured_output.current_trial), '.wav'));
            s.structured_output.add_message(class(s),'audio_filename', filename);
            audiowrite(filename, y, 48000);
            %copyfile('/home/eye/Documents/projects/eyetracking/anonymous_collected_data/phase_1/user5_203_20201113/23.wav',filename);
            
            s.recording = false;
            interaction_map = containers.Map({'exit'}, {ChangeScreen.No});
            if s.mainWindow.live_transcription_active>0
                s.mainWindow.do_live_transcription(filename);
                %s.mainWindow.do_live_transcription('./Test01.wav');
            end
        end    
        
        function draw(s, cumulative_drawing)
            if s.recording
                cumulative_drawing.add_fill_oval(s.depth,[1 0 0], [10 10 s.mainWindow.margin/6 s.mainWindow.margin/6]);
            end
        end
    end

end