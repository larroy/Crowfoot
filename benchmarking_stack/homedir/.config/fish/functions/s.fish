function s --description "Start a command in the background and remove from jobs list"
    echo (count $argv)
    if test (count $argv) -ne 1
        echo "illegal number of parameters"
        return 1
    end
    $argv[1] 2>&1 > /dev/null &
    disown
end

