classdef CumulativeDrawing < handle
    properties
        mainWindow;
        frame_to_draw_all;
        count_frames;
    end
    methods
        function s = CumulativeDrawing(mainWindow)
            s.count_frames = 0;
            s.frame_to_draw_all = 0;
            s.mainWindow = mainWindow;
        end
        function add_fill_rect(s,caller, varargin)
            Screen('FillRect', s.mainWindow.winMain, varargin{:});
        end
        function add_frame_rect(s,caller, varargin)
            Screen('FrameRect', s.mainWindow.winMain, varargin{:});
        end
        
        function nx = add_formatted_text(s,caller, varargin)
            nx = DrawFormattedText(s.mainWindow.winMain, varargin{:});
            if isa(varargin{2}, 'double')
                width = s.mainWindow.character_width*length(varargin{1});
                nx = width+varargin{2};
            else
                nx = None();
            end
        end
        
        function nx = add_text(s,caller, varargin)
            Screen('DrawText', s.mainWindow.winMain,  varargin{:});
        end
        
        function add_line(s,caller, varargin)
            Screen('DrawLine', s.mainWindow.winMain, varargin{:});
        end
        
        function add_fill_oval(s,caller, varargin)
            Screen('FillOval', s.mainWindow.winMain, varargin{:});
        end
        
        function add_frame_oval(s,caller, varargin)
            Screen('FrameOval', s.mainWindow.winMain, varargin{:});
        end
        
        function add_texture(s,caller, varargin)
            Screen('DrawTexture', s.mainWindow.winMain, varargin{:});
        end
        
        function add_textures(s,caller, varargin)
            Screen('DrawTextures', s.mainWindow.winMain, varargin{:});
        end
        
        function add_fill_poly(s,caller, varargin)
            Screen('FillPoly', s.mainWindow.winMain, varargin{:});
        end
        
        
        function reset(s,caller, varargin)
            s.frame_to_draw_all = mod(s.count_frames, 100)==0;
            s.count_frames = s.count_frames + 1;
        end
        
    end
    
end
