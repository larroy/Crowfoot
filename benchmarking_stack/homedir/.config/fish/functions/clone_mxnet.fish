function clone_mxnet
    echo (count $argv)
    if test (count $argv) -ne 1 
        echo "illegal number of parameters"
        return 1
    end
    git clone --recursive git@github.com:larroy/mxnet.git $argv[1]
    cd $argv[1]
    git remote add upstream git@github.com:apache/incubator-mxnet.git
    git remote add edge git@github.com:MXNetEdge/incubator-mxnet.git
    git fetch --all
end
