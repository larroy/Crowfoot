function diffmaster
    git diff (git merge-base (git rev-parse --abbrev-ref HEAD) upstream/master)
end
