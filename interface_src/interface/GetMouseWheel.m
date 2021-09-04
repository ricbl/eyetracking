function wheelDelta = GetMouseWheel()
% wheelDelta = GetMouseWheel([mouseIndex])
%
% Return change of mouse wheel position of a wheel mouse (in "wheel clicks")
% since last query. 'mouseIndex' is the device index of the wheel mouse to
% query. The argument is optional: If left out, the first detected real wheel
% mouse is queried.
%
% OS X: _____________________________________________________________________
%
% Uses PsychHID for low-level access to mice with mouse wheels. If wheel
% state is not queried frequent enough, the internal queue may overflow and
% some mouse wheel movements may get lost, resulting in a smaller reported
% 'wheelDelta' than the real delta since last query. On OS X 10.4.11 the
% operating system can store at most 10 discrete wheel movements before it
% discards movement events. This uses low-level code which may not work on
% all wheel mice.
%
% Linux: ____________________________________________________________________
%
% Uses GetMouse() extra valuators to check if one of the valuators represents
% a mouse wheel, then translates the valuators absolute wheel position into
% wheel delta by keeping track of old values.
%
% MS-Windows: _______________________________________________________________
%
% This function is not supported and will fail with an error.
%
% ___________________________________________________________________________
% See also: GetClicks, GetMouseIndices, GetMouse, SetMouse, ShowCursor,
% HideCursor
%

% History:
% 05/31/08  mk  Initial implementation.
% 05/14/12  mk  Tweaks for more mice.
% 02/21/17  mk  Support Linux by wrapping around GetMouse() valuator functionality.
% 11/22/17  mk  Fix potential OSX bug. Untested on OSX so far.

% Cache the detected index of the first "real" wheel mouse to allow for lower
% execution times:

%https://github.com/kleinerm/Psychtoolbox-3/blob/master/Psychtoolbox/PsychBasic/GetMouseWheel.m
% MIT License

persistent oldWheelAbsolute;
persistent wheelMouseIndex;
persistent index_valinfo;

if isempty(oldWheelAbsolute)
    oldWheelAbsolute = nan(max(GetMouseIndices)+1, 1);
end

if isempty(wheelMouseIndex)
    % Find first mouse with a mouse wheel:
    if IsLinux
        mousedices = GetMouseIndices('slavePointer');
    else
        mousedices = GetMouseIndices;
    end
    numMice = length(mousedices);
    if numMice == 0
        error('GetMouseWheel could not find any mice connected to your computer');
    end

    if IsLinux
        for i=mousedices
            [~,~,~,~,~,valinfo] = GetMouse([], i);
            for j=1:length(valinfo)
               if strcmp(valinfo(j).label, 'Rel Vert Scroll')
                    wheelMouseIndex = i;
                    index_valinfo = j;
                    break;
                end
            end
            if ~isempty(wheelMouseIndex)
                break;
            end
        end
    end

    if isempty(wheelMouseIndex)
        error('GetMouseWheel could not find any mice with mouse wheels connected to your computer');
    end
end;
mouseIndex = wheelMouseIndex;
[~,~,~,~,valuators,valinfo] = GetMouse([], mouseIndex);
wheelAbsolute = valuators(index_valinfo);
if isnan(oldWheelAbsolute(mouseIndex+1))
    wheelDelta = 0;
else
    wheelDelta = wheelAbsolute - oldWheelAbsolute(mouseIndex+1);
end
oldWheelAbsolute(mouseIndex+1) = wheelAbsolute;


keys = [KbName('UpArrow') KbName('DownArrow') KbName('Space')];

[keyDown, ~, keyCode] = KbCheck;
if keyDown
    if keyCode(KbName('UpArrow'))
        wheelDelta = wheelDelta - 15;
    elseif keyCode(KbName('DownArrow'))
        wheelDelta = wheelDelta + 15;
    end    
end
return;
