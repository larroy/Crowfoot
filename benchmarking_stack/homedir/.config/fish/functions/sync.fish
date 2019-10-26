function sync --description "rsync with nice flags"
    rsync -zvaP --exclude "*.swp" --exclude "*~" $argv
end
