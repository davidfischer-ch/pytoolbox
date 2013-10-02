# Sample Python 2 -> 3 conversion of Pyutils
rsync -ah --progress --delete pytoolbox/ pytoolbox3/ && 2to3 -x import -w pytoolbox3
