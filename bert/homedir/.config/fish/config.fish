set -x PATH $HOME/bin $HOME/.toolbox/bin $PATH $HOME/bin/platform-tools
set -x EDITOR vim
switch (uname)
    case Linux
        set ls_command "ls"
    case Darwin
        set ls_command "gls"
    case '*'
        set ls_command "ls"
end

function l
    eval $ls_command -lF --group-directories-first --color $argv
end

function lt
    eval $ls_command -lFrt --group-directories-first --color $argv
end

function lS
    eval $ls_command -rlS ---group-directories-first -color $argv
end

function la
    eval $ls_command -lA --group-directories-first --color $argv
end

function ll
    eval $ls_command -lA --group-directories-first --color $argv
end

function prompt_hostname
    set_color yellow
    echo $hostname
    set_color normal
end

function fish_prompt --description 'Write out the prompt'
    set -l last_status $status
	set -l color_cwd
    set -l suffix
    if not set -q __git_cb
        set __git_cb " ["(set_color brmagenta)(git branch ^/dev/null | grep \* | sed 's/* //')(set_color normal)"]"
    end
    switch "$USER"
        case root toor
            if set -q fish_color_cwd_root
                set color_cwd $fish_color_cwd_root
            else
                set color_cwd $fish_color_cwd
            end
            set suffix '#'
        case '*'
            set color_cwd $fish_color_cwd
            set suffix '>'
    end

    echo -n -s "$USER" @ (prompt_hostname) ':' "$last_status" ':' ' ' (set_color $color_cwd) (prompt_pwd) (set_color normal) $__git_cb "$suffix "
end
